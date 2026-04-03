-- A function that returns all records matching a pattern
CREATE OR REPLACE FUNCTION search_contacts_by_pattern(search_pattern TEXT)
RETURNS TABLE (id INT, name VARCHAR, phone VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.name, c.phone
    FROM contacts c
    WHERE c.name ILIKE '%' || search_pattern || '%' 
       OR c.phone ILIKE '%' || search_pattern || '%';
END;
$$ LANGUAGE plpgsql;

-- A function that queries data from the table with pagination
CREATE OR REPLACE FUNCTION get_contacts_paged(p_limit INT, p_offset INT)
RETURNS TABLE (id INT, name VARCHAR, phone VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.name, c.phone
    FROM contacts AS c
    ORDER BY c.id
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;