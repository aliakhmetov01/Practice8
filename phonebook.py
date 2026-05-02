import psycopg2
import csv
import json
from config import load_config
from connect import connect

def run_db_query(query, params=None, is_procedure=False, fetch_results=False):
    conn = None
    results = None
    try:
        config = load_config()
        conn = connect(config)
        cur = conn.cursor()
        if is_procedure:
            cur.execute(f"CALL {query}", params)
        else:
            cur.execute(query, params)
            if fetch_results:
                results = cur.fetchall()
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка БД: {error}")
    finally:
        if conn is not None:
            conn.close()
    return results


def advanced_search():
    print("\n1. Фильтр по группе\n2. Поиск по Email\n3. Сортировка (имя/дата)")
    sub_choice = input("Выберите тип поиска: ")
    
    if sub_choice == '1':
        group = input("Введите название группы: ")
        rows = run_db_query("SELECT * FROM contacts WHERE contact_group ILIKE %s", (f"%{group}%",), fetch_results=True)
    elif sub_choice == '2':
        email = input("Введите часть email (например, gmail): ")
        rows = run_db_query("SELECT * FROM contacts WHERE email ILIKE %s", (f"%{email}%",), fetch_results=True)
    elif sub_choice == '3':
        sort_col = input("Сортировать по (name, birthday, created_at): ")
        rows = run_db_query(f"SELECT * FROM contacts ORDER BY {sort_col}", fetch_results=True)
    
    if rows:
        for r in rows: print(r)
    else:
        print("Ничего не найдено.")

def paginated_navigation():
    """Реализация пункта 3.2.4: навигация next/prev/quit"""
    limit = 5
    offset = 0
    while True:
        query = "SELECT * FROM get_contacts_paged(%s::int, %s::int)"
        rows = run_db_query(query, (limit, offset), fetch_results=True)
        
        print(f"\n--- Страница (пропущено {offset}) ---")
        for row in rows:
            print(f"ID: {row[0]} | Имя: {row[1]} | Тел: {row[2]}")
        
        cmd = input("\n[n]ext / [p]rev / [q]uit: ").lower()
        if cmd == 'n':
            if len(rows) == limit: offset += limit
            else: print("Это последняя страница.")
        elif cmd == 'p':
            offset = max(0, offset - limit)
        elif cmd == 'q':
            break


def export_to_json():
    """Пункт 3.3.1: Экспорт всех контактов в JSON"""
    rows = run_db_query("SELECT * FROM contacts", fetch_results=True)
    contacts = []
    for r in rows:
        contacts.append({"id": r[0], "name": r[1], "phone": r[2]})
    
    with open("contacts.json", "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=4, ensure_ascii=False)
    print("Данные успешно экспортированы в contacts.json")

def import_from_json():
    """Пункт 3.3.2: Импорт из JSON с проверкой дубликатов"""
    try:
        with open("contacts.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        for entry in data:
            exists = run_db_query("SELECT id FROM contacts WHERE name = %s", (entry['name'],), fetch_results=True)
            if exists:
                act = input(f"Контакт {entry['name']} уже есть. [s]kip / [o]verwrite? ")
                if act == 's': continue
            
            run_db_query("upsert_contact(%s, %s)", (entry['name'], entry['phone']), is_procedure=True)
        print("Импорт завершен.")
    except FileNotFoundError:
        print("Файл contacts.json не найден.")

def search_by_pattern():
    pattern = input("Введите часть имени или номера: ").strip()
    rows = run_db_query("SELECT * FROM search_contacts_by_pattern(%s)", (pattern,), fetch_results=True)
    if rows:
        for row in rows: print(f"ID: {row[0]} | Имя: {row[1]} | Тел: {row[2]}")
    else: print("Ничего не найдено.")

def upsert_user():
    name = input("Имя: ").strip()
    phone = input("Телефон: ").strip()
    run_db_query("upsert_contact(%s, %s)", (name, phone), is_procedure=True)
    print("Готово!")

def load_from_csv(filepath):
    names, phones = [], []
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    names.append(row[0].strip())
                    phones.append(row[1].strip())
        run_db_query("bulk_insert_with_validation(%s, %s)", (names, phones), is_procedure=True)
        print("Загрузка из CSV завершена.")
    except Exception as e: print(f"Ошибка CSV: {e}")

def delete_flexible():
    target = input("Введите имя или номер для удаления: ").strip()
    run_db_query("delete_contact_flexible(%s)", (target,), is_procedure=True)
    print(f"Запрос на удаление '{target}' выполнен.")

if __name__ == '__main__':
    while True:
        print("\n--- PhoneBook Advanced ---")
        print("1. Поиск контактов (простой)")
        print("2. Добавить/Обновить")
        print("3. Импорт из CSV")
        print("4. Навигация (Next/Prev)")
        print("5. Удалить")
        print("6. Расширенный поиск (Filter/Sort)")
        print("7. Экспорт в JSON")
        print("8. Импорт из JSON")
        print("0. Выход")
        
        choice = input("Выберите: ")
        if choice == '1': search_by_pattern()
        elif choice == '2': upsert_user()
        elif choice == '3': load_from_csv("data.csv")
        elif choice == '4': paginated_navigation()
        elif choice == '5': delete_flexible()
        elif choice == '6': advanced_search()
        elif choice == '7': export_to_json()
        elif choice == '8': import_from_json()
        elif choice == '0': break