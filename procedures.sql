CREATE OR REPLACE PROCEDURE upsert_contact(p_name TEXT, p_phone TEXT)
AS $$
BEGIN
    INSERT INTO contacts (name, phone)
    VALUES (p_name, p_phone)
    ON CONFLICT (name) 
    DO UPDATE SET phone = EXCLUDED.phone;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE bulk_insert_with_validation(
    p_names TEXT[], 
    p_phones TEXT[],
    INOUT p_errors TEXT[] DEFAULT '{}'
)
AS $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1 .. array_upper(p_names, 1) LOOP
        IF p_phones[i] ~ '^\+?\d{7,15}$' THEN
            INSERT INTO contacts (name, phone)
            VALUES (p_names[i], p_phones[i])
            ON CONFLICT (phone) DO NOTHING;
        ELSE
            p_errors := array_append(p_errors, p_names[i] || ' (Invalid phone: ' || p_phones[i] || ')');
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE delete_contact_flexible(p_identifier TEXT)
AS $$
BEGIN
    DELETE FROM contacts 
    WHERE name = p_identifier OR phone = p_identifier;
END;
$$ LANGUAGE plpgsql;