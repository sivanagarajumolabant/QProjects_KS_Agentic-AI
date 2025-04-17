CREATE OR REPLACE PROCEDURE update_bonus (
    p_emp_id IN NUMBER, p_emp_id1 IN NUMBER
)
AS
    v_salary         NUMBER;
    v_bonus          NUMBER;
    v_exists         NUMBER;
    CURSOR emp_cur IS
        SELECT emp_id, salary FROM employees WHERE department_id = 10;
BEGIN
    -- Check if employee exists
    SELECT COUNT(*) INTO v_exists FROM employees WHERE emp_id = p_emp_id;
	
    IF v_exists = 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'Employee not found.');
    END IF;
	select * from Siva;
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
	-- added extra
	select * from himalaya;
    -- Update bonus
    UPDATE employees SET bonus = v_bonus WHERE emp_id = p_emp_id;
	
	IF siva = 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'Employee not found.');
    END IF;
	
    -- Log update
    INSERT INTO bonus_log(emp_id, bonus, log_date)
    VALUES (p_emp_id, v_bonus, SYSDATE);

    -- Loop example
    FOR rec IN emp_cur LOOP
        DBMS_OUTPUT.PUT_LINE('Emp ID: ' || rec.emp_id || ' Salary: ' || rec.salary);
    END LOOP;

    COMMIT;

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        DBMS_OUTPUT.PUT_LINE('No employee found.');
    WHEN OTHERS THEN
        ROLLBACK;
        DBMS_OUTPUT.PUT_LINE('Unexpected error: ' || SQLERRM);
END;
