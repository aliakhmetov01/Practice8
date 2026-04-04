import psycopg2
import csv
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


def search_by_pattern():
    pattern = input("Введите часть имени или номера: ").strip()

    rows = run_db_query("SELECT * FROM search_contacts_by_pattern(%s)", (pattern,), fetch_results=True)
    
    if rows:
        for row in rows:
            print(f"ID: {row[0]} | Имя: {row[1]} | Тел: {row[2]}")
    else:
        print("Ничего не найдено.")


def upsert_user():
    name = input("Имя: ").strip()
    phone = input("Телефон: ").strip()
    run_db_query("upsert_contact(%s, %s)", (name, phone), is_procedure=True)
    print("Готово!")


def load_from_csv(filepath):
    """Читает CSV и отправляет данные в процедуру массовой вставки"""
    names = []
    phones = []
    
    try:
        # 1. Читаем данные из файла в списки
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    names.append(row[0].strip())
                    phones.append(row[1].strip())


        run_db_query("bulk_insert_with_validation(%s, %s)", (names, phones), is_procedure=True)
        
        print(f"Файл '{filepath}' обработан через SQL-процедуру.")
        print("Валидация выполнена на стороне базы данных.")

    except FileNotFoundError:
        print(f"Ошибка: Файл '{filepath}' не найден.")
    except Exception as error:
        print(f"Ошибка при массовой загрузке: {error}")

def get_paged():
    print("\n--- Просмотр списка по страницам ---")
    try:

        limit_val = int(input("Сколько контактов вывести на экран? (LIMIT): "))
        offset_val = int(input("Сколько контактов пропустить? (OFFSET): "))

        query = "SELECT * FROM get_contacts_paged(%s::int, %s::int)"
        rows = run_db_query(query, (limit_val, offset_val), fetch_results=True)

        if rows:
            print(f"\nПоказано результатов: {len(rows)}")
            for row in rows:
                print(f"ID: {row[0]} | Имя: {row[1]} | Тел: {row[2]}")
        else:
            print("На этой странице данных нет.")
            
    except ValueError:
        print("Ошибка: Нужно вводить только целые числа!")
    except Exception as e:
        print(f"Ошибка при пагинации: {e}")


def delete_flexible():
    target = input("Введите имя или номер для удаления: ").strip()
    run_db_query("delete_contact_flexible(%s)", (target,), is_procedure=True)
    print(f"Запрос на удаление '{target}' выполнен.")

if __name__ == '__main__':
    while True:
        print("\n--- PhoneBook ---")
        print("1. Поиск контактов")
        print("2. Добавить/Обновить")
        print("3. Добавить несколько контакотов ")
        print("4. Просмотр контактов(список)")
        print("5. Удалить (имя/номер)")
        print("0. Выход")
        
        choice = input("Выберите: ")
        if choice == '1': search_by_pattern()
        elif choice == '2': upsert_user()
        elif choice == '3': load_from_csv("data.csv")
        elif choice == '4': get_paged()
        elif choice == '5': delete_flexible()
        elif choice == '0': break