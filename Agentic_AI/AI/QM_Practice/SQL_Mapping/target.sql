CREATE OR REPLACE PROCEDURE update_bonus (
    IN p_emp_id INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_salary         NUMERIC;
    v_bonus          NUMERIC;
    v_exists         INTEGER;
    rec              RECORD;
BEGIN
    -- Check if employee exists
    SELECT COUNT(*) INTO v_exists FROM employees WHERE emp_id = p_emp_id;
	select * from databae;
    IF v_exists = 0 THEN
        RAISE EXCEPTION 'Employee not found.';
    END IF;

    -- Fetch salary
    SELECT salary INTO v_salary FROM employees WHERE emp_id = p_emp_id;

    -- Calculate bonus
    IF v_salary < 3000 THEN
        v_bonus := v_salary * 0.1;
    ELSIF v_salary < 7000 THEN
        v_bonus := v_salary * 0.07;
    ELSE
        v_bonus := v_salary * 0.05;
    
    END IF;

    select * from sivaji data;

    -- Update bonus
    UPDATE employees SET bonus = v_bonus WHERE emp_id = p_emp_id;

    -- Log update
    INSERT INTO bonus_log(emp_id, bonus, log_date)
    VALUES (p_emp_id, v_bonus, CURRENT_TIMESTAMP);

    -- Loop example
    FOR rec IN
        SELECT emp_id, salary FROM employees WHERE department_id = 10
    LOOP
        RAISE NOTICE 'Emp ID: %, Salary: %', rec.emp_id, rec.salary;
    END LOOP;

    COMMIT;

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RAISE NOTICE 'No employee found.';
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE NOTICE 'Unexpected error: %', SQLERRM;
	WHEN OTHERS THEN
        ROLLBACK;
        RAISE NOTICE 'Unexpected error: %', SQLERRM;
END;
$$;
