CREATE OR REPLACE PROCEDURE HR.manage_hr_data AS 
BEGIN
    INSERT INTO employees VALUES (300, 'John', 'Doe', 'jdoe@example.com', '515-555-1234', SYSDATE, 'IT_PROG', 6000, 103, 60);  
    INSERT INTO employees VALUES (301, 'Jane', 'Smith', 'jsmith@example.com', '515-555-5678', SYSDATE, 'ST_CLERK', 4000, 120, 50);  
    INSERT INTO employees VALUES (302, 'Alice', 'Brown', 'aliceb@example.com', '515-555-1111', SYSDATE, 'HR_REP', 4500, 101, 40);  
    INSERT INTO employees VALUES (303, 'Mike', 'Johnson', 'mikej@example.com', '515-555-2222', SYSDATE, 'IT_PROG', 7500, 103, 60);  
    INSERT INTO employees VALUES (304, 'Sara', 'Davis', 'sarad@example.com', '515-555-3333', SYSDATE, 'AD_ASST', 3000, 101, 30);  
    INSERT INTO employees VALUES (305, 'David', 'Wilson', 'davidw@example.com', '515-555-4444', SYSDATE, 'SA_REP', 9000, 145, 80);  
    INSERT INTO employees VALUES (306, 'Emily', 'Taylor', 'emilyt@example.com', '515-555-5555', SYSDATE, 'AC_ACCOUNT', 5000, 205, 110);  
    INSERT INTO employees VALUES (307, 'Luke', 'White', 'lukew@example.com', '515-555-6666', SYSDATE, 'MK_REP', 4200, 201, 20);  
    INSERT INTO employees VALUES (308, 'Anna', 'Hall', 'annah@example.com', '515-555-7777', SYSDATE, 'HR_REP', 4600, 101, 40);  
    INSERT INTO employees VALUES (309, 'Robert', 'Lee', 'robertl@example.com', '515-555-8888', SYSDATE, 'FI_ACCOUNT', 5800, 205, 110);  


    UPDATE employees SET salary = salary * 1.10 WHERE department_id = 60;  
    UPDATE employees SET salary = salary * 1.05 WHERE employee_id = 301;  
    UPDATE employees SET salary = salary + 1000 WHERE job_id = 'HR_REP';  
    UPDATE employees SET salary = salary * 1.02 WHERE job_id = 'IT_PROG';  
    UPDATE employees SET salary = salary - 500 WHERE department_id = 80;  
    UPDATE employees SET salary = salary * 1.08 WHERE job_id = 'SA_REP';  
    UPDATE employees SET salary = 7000 WHERE employee_id = 305;  
    UPDATE employees SET salary = salary + 250 WHERE job_id = 'MK_REP';  
    UPDATE employees SET salary = salary * 1.07 WHERE department_id = 40;  
    UPDATE employees SET salary = salary + 500 WHERE employee_id = 309;  


    DELETE FROM employees WHERE employee_id = 300;  
    DELETE FROM employees WHERE employee_id = 302;  
    DELETE FROM employees WHERE employee_id = 308;  
    DELETE FROM employees WHERE salary > 15000;  
    DELETE FROM employees WHERE department_id = 30;  
    DELETE FROM employees WHERE email LIKE 'test%';  
    DELETE FROM employees WHERE first_name = 'Robert' AND last_name = 'Lee';  
    DELETE FROM employees WHERE employee_id IN (307, 309);  
    DELETE FROM employees WHERE salary < 3500;  
    DELETE FROM employees WHERE job_id = 'AC_ACCOUNT';  


    INSERT INTO departments VALUES (280, 'Cyber Security', 108, 1700);  
    INSERT INTO departments VALUES (290, 'Data Science', 109, 1800);  
    INSERT INTO departments VALUES (300, 'AI Research', 110, 1900);  
    INSERT INTO departments VALUES (310, 'Blockchain Development', 111, 2000);  
    INSERT INTO departments VALUES (320, 'Cloud Computing', 112, 2100);  
    INSERT INTO departments VALUES (330, 'DevOps', 113, 2200);  
    INSERT INTO departments VALUES (340, 'Machine Learning', 114, 2300);  
    INSERT INTO departments VALUES (350, 'Product Management', 115, 2400);  
    INSERT INTO departments VALUES (360, 'Cyber Intelligence', 116, 2500);  
    INSERT INTO departments VALUES (370, 'Software Development', 117, 2600);  


    UPDATE departments SET department_name = 'Cloud & AI' WHERE department_id = 320;  
    UPDATE departments SET department_name = 'DevOps & Automation' WHERE department_id = 330;  
    UPDATE departments SET department_name = 'Cyber Security & Intelligence' WHERE department_id = 360;  
    UPDATE departments SET department_name = 'Software Engineering' WHERE department_id = 370;  
    UPDATE departments SET department_name = 'AI & Data Science' WHERE department_id = 290;  
    UPDATE departments SET department_name = 'Web Development' WHERE department_id = 280;  
    UPDATE departments SET department_name = 'Product Strategy' WHERE department_id = 350;  
    UPDATE departments SET department_name = 'Blockchain Solutions' WHERE department_id = 310;  
    UPDATE departments SET department_name = 'AI Research & Innovation' WHERE department_id = 300;  
    UPDATE departments SET department_name = 'Cloud Security' WHERE department_id = 320;  

    INSERT INTO jobs VALUES ('SEC_ANA', 'Security Analyst', 5000, 12000);  
    INSERT INTO jobs VALUES ('DATA_SCI', 'Data Scientist', 7000, 15000);  
    INSERT INTO jobs VALUES ('AI_ENG', 'AI Engineer', 7500, 16000);  
    INSERT INTO jobs VALUES ('CLOUD_ARCH', 'Cloud Architect', 8000, 17000);  
    INSERT INTO jobs VALUES ('DEVOPS', 'DevOps Engineer', 6000, 14000);  
    INSERT INTO jobs VALUES ('BLOCK_DEV', 'Blockchain Developer', 7000, 18000);  
    INSERT INTO jobs VALUES ('WEB_DEV', 'Web Developer', 4500, 12000);  
    INSERT INTO jobs VALUES ('UX_DES', 'UX Designer', 5500, 12500);  
    INSERT INTO jobs VALUES ('PROD_MGR', 'Product Manager', 8500, 20000);  
    INSERT INTO jobs VALUES ('CYBER_INT', 'Cyber Intelligence Analyst', 7500, 16000);  

    SELECT * FROM employees WHERE salary > 8000;  
    SELECT * FROM employees WHERE job_id = 'IT_PROG';  
    SELECT * FROM employees WHERE department_id = 60;  
    SELECT * FROM employees WHERE hire_date > ADD_MONTHS(SYSDATE, -12);  
    SELECT * FROM employees WHERE job_id IN ('DATA_SCI', 'AI_ENG');  


    FOR i IN 1..30 LOOP  
        INSERT INTO employees VALUES (400 + i, 'Test' || i, 'User', 'test' || i || '@example.com', '515-555-' || (3000 + i), SYSDATE, 'ST_CLERK', 3500, 120, 50);  
        UPDATE employees SET salary = salary + 200 WHERE employee_id = 400 + i;  
        DELETE FROM employees WHERE MOD(employee_id, 2) = 0;  
    END LOOP;  

    COMMIT;  
    DBMS_OUTPUT.PUT_LINE('HR data management completed successfully.');  
EXCEPTION  
    WHEN OTHERS THEN  
        DBMS_OUTPUT.PUT_LINE('Error: ' || SQLERRM);  
        ROLLBACK;  
END manage_hr_data;  