
  CREATE OR REPLACE  PROCEDURE "ADT"."P_ADDCOVIDPATIENTDETAILS" (IV_IPNUM                    IN VARCHAR2,
                                                         IV_UHID                     IN VARCHAR2,
                                                         IV_NOCOVID_VACCINE_RECIEVED IN VARCHAR2,
                                                         IV_1STDOSAGE_VACCINE        IN VARCHAR2,
                                                         IV_1STDOSAGE_VACCINE_NAME   IN VARCHAR2,
                                                         IV_1STDOSAGE_DATE           IN VARCHAR2,
                                                         IV_2NDDOSAGE_VACCINE        IN VARCHAR2,
                                                         IV_2NDDOSAGE_VACCINE_NAME   IN VARCHAR2,
                                                         IV_2NDDOSAGE_DATE           IN VARCHAR2,
                                                         IV_NO_KNOWN_COVID_INFECTION IN VARCHAR2,
                                                         IV_CURRENT_COVID_INFECTION  IN VARCHAR2,
                                                         IV_PAST_COVID_INFECTION     IN VARCHAR2,
                                                         IV_DATE_LAST_RTPCR          IN VARCHAR2,
                                                         IV_TEST_STATUS              IN VARCHAR2,
                                                         IV_ADD_REMARK               IN VARCHAR2,
                                                         IV_LOCATIONID               IN VARCHAR2,
                                                         IV_LOGINID                  IN VARCHAR2) AS
  /******************************************************************************
    Procedure    :  P_ADDCOVIDPATIENTDETAILS
    Parameters   :
    Purpose      :  This procedure is to save the Covid Patient details
    Created By   :
    Table Used   :  covid_patient_details

    DateModified :
    Modifiedby   :
    Modifications:
  ******************************************************************************/
  FIRST_DOSAGE           varchar2(50);
  SECOND_DOSAGE          varchar2(50);
  VACCINE_TESTING_STSTUS VARCHAR2(50);

BEGIN
  IF UPPER(IV_1STDOSAGE_VACCINE_NAME) = 'SELECT' THEN
    FIRST_DOSAGE := '';
  else
    FIRST_DOSAGE := IV_1STDOSAGE_VACCINE_NAME;
  END IF;
  IF UPPER(IV_2NDDOSAGE_VACCINE_NAME) = 'SELECT' THEN
    SECOND_DOSAGE := '';
  else
    SECOND_DOSAGE := IV_2NDDOSAGE_VACCINE_NAME;
  END IF;



  INSERT INTO adt.covid_patient_details_adm
    (IPNUMBER,
     UHID,
     NOCOVID_VACCINE_RECIEVED,
     FIRST_DOSAGE_VACCINE,
     FIRST_DOSAGE_VACCINE_NAME,
     FIRST_DOSAGE_DATE,
     SECOND_DOSAGE_VACCINE,
     SECOND_DOSAGE_VACCINE_NAME,
     SECOND_DOSAGE_DATE,
     NO_KNOWN_COVID_INFECTION,
     CURRENT_COVID_INFECTION,
     PAST_COVID_INFECTION,
     DATE_LAST_RTPCR,
     TEST_STATUS,
     ADD_REMARK,
     STATUS,
     CREATEDDATE,
     LOCATIONID,
     LOGINID,
     UPDATEDDATE,
     UPDATEDBY)
  VALUES
    (IV_IPNUM,
     IV_UHID,
     IV_NOCOVID_VACCINE_RECIEVED,
     IV_1STDOSAGE_VACCINE,
     FIRST_DOSAGE,
     to_date((IV_1STDOSAGE_DATE), 'DD/MM/YYYY'),
     IV_2NDDOSAGE_VACCINE,
     SECOND_DOSAGE,
     to_date((IV_2NDDOSAGE_DATE), 'DD/MM/YYYY'),
     IV_NO_KNOWN_COVID_INFECTION,
     IV_CURRENT_COVID_INFECTION,
     IV_PAST_COVID_INFECTION,
     IV_DATE_LAST_RTPCR,
     VACCINE_TESTING_STSTUS,
     IV_ADD_REMARK,
     1,
     SYSDATE,
     IV_LOCATIONID,
     IV_LOGINID,
     '',
     '');

  commit;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE(SQLCODE || SQLERRM);

END P_ADDCOVIDPATIENTDETAILS;









