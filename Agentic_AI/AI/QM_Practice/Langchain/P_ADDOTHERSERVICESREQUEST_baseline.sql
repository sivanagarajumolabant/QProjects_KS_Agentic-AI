CREATE OR REPLACE PROCEDURE DBO."P_ADDOTHERSERVICESREQUEST" (ICLOB_OTHRTSERVICESREQUEST  IN CLOB,
                                                      ON_OTHERSERVICEREQUSETNO    OUT otherservicesmaster.otherservicesrequestno%TYPE,
                                                      OCURSOR_OTHERSERVICEDETAILS OUT SYS_REFCURSOR,
                                                      OCURSOR_OTHERSERVICESTATUS  OUT SYS_REFCURSOR) IS
  LXML_RADIOLOGYREQUEST    XMLTYPE;
  V_otherservicesrequestno OTHERSERVICESMASTER.OTHERSERVICESREQUESTNO%TYPE;
  V_LOGINID                OTHERSERVICESMASTER.CREATEDBY%TYPE;
  V_UHID                   OTHERSERVICESMASTER.UHID%TYPE;
  v_LocationId             OTHERSERVICESMASTER.LOCATIONID%TYPE;
  V_IPNumber               OTHERSERVICESMASTER.IPNUMBER%TYPE;
  V_NEWREQUESTNO           OTHERSERVICESMASTER.OTHERSERVICESREQUESTNO%TYPE := NULL;
  V_INDEX                  XMLTYPE;
  I                        BINARY_INTEGER := 1;
  V_SERVICEITEM            OTHERSERVICEDETAILS.SERVICEITEMID%TYPE;
  V_COUNT                  INTEGER := 0;
  --V_ARR VARCHAR2(200);
  V_PatientServiceID OTHERSERVICESMASTER.Patientserviceid%Type := null;
  --V_DOCTORID  OTHERSERVICESMASTER.Doctorid%Type:=null;

BEGIN
/*  INSERT INTO wards.TEST t VALUES (ICLOB_OTHRTSERVICESREQUEST,sysdate,1,1);
  commit;*/
  
  LXML_RADIOLOGYREQUEST := XMLTYPE(ICLOB_OTHRTSERVICESREQUEST);
  V_LOGINID             := LXML_RADIOLOGYREQUEST.EXTRACT('/OtherServiceRequest/OtherService/@CreatedBy')
                           .getstringval();
  V_UHID                := LXML_RADIOLOGYREQUEST.EXTRACT('/OtherServiceRequest/OtherService/@UHID')
                           .getstringval();
  v_LocationId          := LXML_RADIOLOGYREQUEST.extract('/OtherServiceRequest/OtherService/@LocationID')
                           .getstringval();
  V_IPNumber            := LXML_RADIOLOGYREQUEST.EXTRACT('/OtherServiceRequest/OtherService/@IPNumber')
                           .getstringval();
  V_PatientServiceID    := LXML_RADIOLOGYREQUEST.EXTRACT('/OtherServiceRequest/OtherService/@Patientserviceid')
                           .getnumberval();
 -- V_DOCTORID            :=  LXML_RADIOLOGYREQUEST.EXTRACT('/OtherServiceRequest/OtherService/@DOCTORID')
                          -- .getnumberval();
  BEGIN
    IF V_PatientServiceID = 1 THEN
      SELECT OM.OTHERSERVICESREQUESTNO
        INTO V_NEWREQUESTNO
        FROM OTHERSERVICESMASTER OM
       WHERE OM.IPNUMBER = V_IPNumber
         AND OM.LOCATIONID = v_LocationId
         AND OM.STATUS = 1
         AND ROWNUM = 1;
    END IF;
  EXCEPTION
    /* WHEN NO_DATA_FOUND THEN
    V_NEWREQUESTNO := NULL;*/
    WHEN OTHERS THEN
      V_NEWREQUESTNO := NULL;
  END;
  IF V_NEWREQUESTNO IS NULL THEN
    SELECT S_OTHERSERVICESREQUESTNO.NEXTVAL
      INTO V_otherservicesrequestno
      FROM DUAL;
    ON_OTHERSERVICEREQUSETNO := V_otherservicesrequestno;
    INSERT INTO OTHERSERVICESMASTER
      (OTHERSERVICESREQUESTNO,
       CREATEDBY,
       CREATEDDATE,
       STATUS,
       UHID,
       IPNUMBER,
       LOCATIONID,
       REQUESTSTATUS,
       REQUESTEDBY,
       PatientServiceID
      -- DoctorID
      )
    VALUES
      (V_otherservicesrequestno,
       V_LOGINID,
       SYSDATE,
       1,
       V_UHID,
       V_IPNumber,
       v_LocationId,
       1,
       V_LOGINID,
       V_PatientServiceID
       --V_DoctorID
       );
    INSERT INTO OTHERSERVICEDETAILS
      (OTHERSERVICEDETAILID,
       OTHERSERVICESREQUESTNO,
       CREATEDBY,
       CREATEDDATE,
       STATUS,
       DEPTID,
       LOCATIONID,
       COMMENTS,
       QUANTITY,
       PRIORITYID,
       REFERRALDOCTOR,
       SERVICEITEMID,
       STARTDATETIME,
       REQUESTSTATUS,
       REQUIREDAT,
       APPOINTMENTID)
      SELECT S_REQUESTDETAILNO.NEXTVAL,
             V_otherservicesrequestno,
             V_LOGINID,
             SYSDATE,
             1,
             EXTRACT                  (VALUE(le), '/OtherServiceDetails/@DepartmentID'                  )
             .getNUMBERval(),
             v_LocationId,
             EXTRACT                  (VALUE(le), '/OtherServiceDetails/@Comments'                  )
             .getSTRINGval(),
             --EXTRACT(VALUE(le), '/OtherServiceDetails/@Quantity').getNUMBERval(),
             decode(EXTRACT(VALUE(le), '/OtherServiceDetails/@Quantity')
                    .getnumberval(),
                    null,
                    1,
                    EXTRACT(VALUE(le), '/OtherServiceDetails/@Quantity')
                    .getnumberval()),
             /* EXTRACT(VALUE(le), '/OtherServiceDetails/@PriorityID').getNUMBERval(), */
             decode(EXTRACT(VALUE(le), '/OtherServiceDetails/@PriorityID')
                    .getnumberval(),
                    '0',
                    NULL,
                    EXTRACT(VALUE(le), '/OtherServiceDetails/@PriorityID')
                    .getnumberval()),
             /* EXTRACT(VALUE(le), '/OtherServiceDetails/@ReferralDoctorID').getNUMBERval(), */
             decode(EXTRACT(VALUE(le), '/OtherServiceDetails/@ReferralDoctorID')
                    .getnumberval(),
                    '0',
                    NULL,
                    EXTRACT(VALUE(le), '/OtherServiceDetails/@ReferralDoctorID')
                    .getnumberval()),
                    EXTRACT(VALUE(le), '/OtherServiceDetails/@ServiceItemID')
             .getNUMBERval(),
             TO_DATE(EXTRACT(VALUE(le), '/OtherServiceDetails/@StartDateTime')
                     .getSTRINGVAL(),
                     'DD-Mon-yyyy HH24:MI:SS'),
             1,
             /*EXTRACT(VALUE(le), '/OtherServiceDetails/@RequiredAt').getNUMBERval()*/
             decode(EXTRACT(VALUE(le), '/OtherServiceDetails/@RequiredAt')
                    .getnumberval(),
                    '0',
                    NULL,
                    EXTRACT(VALUE(le), '/OtherServiceDetails/@RequiredAt')
                    .getnumberval()),
             EXTRACT(VALUE(le), '/OtherServiceDetails/@AppointmentID')
             .getNUMBERval()
        FROM TABLE(XMLSEQUENCE(EXTRACT(LXML_RADIOLOGYREQUEST,
                                       '/OtherServiceRequest/OtherService/OtherRequestDetails/OtherServiceDetails'))) le;
    OPEN OCURSOR_OTHERSERVICEDETAILS FOR
      SELECT OD.OTHERSERVICEDETAILID,
             OD.OTHERSERVICESREQUESTNO,
             OD.DEPTID,
             OD.PRIORITYID,
             OD.SERVICEITEMID SERVICEID,
             OD.STARTDATETIME,
             F_GETSTATUSMEANING(OD.REQUESTSTATUS,
                                'OTHERSERVICEDETAILS',
                                'REQUESTSTATUS') REQUESTSTATUS
        FROM OTHERSERVICEDETAILS OD
       WHERE OD.STATUS = 1
         AND OD.LOCATIONID = v_LocationId
         AND OD.OTHERSERVICESREQUESTNO = V_otherservicesrequestno;
    OPEN OCURSOR_OTHERSERVICESTATUS FOR
      SELECT OM.OTHERSERVICESREQUESTNO,
             F_GETSTATUSMEANING(OM.REQUESTSTATUS,
                                'OTHERSERVICESMASTER',
                                'REQUESTSTATUS') REQUESTSTATUS
        FROM OTHERSERVICESMASTER OM
       WHERE OM.STATUS = 1
         AND OM.LOCATIONID = v_LocationId
         AND OM.OTHERSERVICESREQUESTNO = V_otherservicesrequestno;
  ELSE
    LOOP
      V_INDEX := LXML_RADIOLOGYREQUEST.EXTRACT('/OtherServiceRequest/OtherService/OtherRequestDetails/OtherServiceDetails[' || I || ']');
      EXIT WHEN V_INDEX IS NULL;
      V_SERVICEITEM := V_INDEX.EXTRACT('/OtherServiceDetails/@ServiceItemID')
                       .GETNUMBERVAL();
      SELECT COUNT(rowid)
        INTO V_COUNT
        FROM OTHERSERVICEDETAILS OD
       WHERE OD.STATUS = 1
         AND OD.LOCATIONID = v_LocationId
         AND OD.SERVICEITEMID = V_SERVICEITEM
         AND OD.OTHERSERVICESREQUESTNO = V_NEWREQUESTNO;
      IF V_COUNT = 0 THEN
        /*IF LENGTH(V_ARR) IS NULL THEN
        V_ARR := V_SERVICEITEM;
        UPDATE OTHERSERVICESMASTER OM
        SET OM.REQUESTSTATUS = 1
        WHERE OM.OTHERSERVICESREQUESTNO = V_NEWREQUESTNO AND
        OM.LOCATIONID = v_LocationId AND OM.STATUS = 1;
        ELSE
        V_ARR := V_ARR || ',' || V_SERVICEITEM;
        END IF;*/
        INSERT INTO OTHERSERVICEDETAILS
          (OTHERSERVICEDETAILID,
           OTHERSERVICESREQUESTNO,
           CREATEDBY,
           CREATEDDATE,
           STATUS,
           DEPTID,
           LOCATIONID,
           COMMENTS,
           QUANTITY,
           PRIORITYID,
           REFERRALDOCTOR,
           SERVICEITEMID,
           STARTDATETIME,
           REQUESTSTATUS,
           REQUIREDAT,
           APPOINTMENTID)
          SELECT S_REQUESTDETAILNO.NEXTVAL,
                 V_NEWREQUESTNO,
                 V_LOGINID,
                 SYSDATE,
                 0,
                 EXTRACT                  (VALUE(le), '/OtherServiceDetails/@DepartmentID'                  )
                 .getNUMBERval(),
                 v_LocationId,
                 EXTRACT                  (VALUE(le), '/OtherServiceDetails/@Comments'                  )
                 .getSTRINGval(),
                 --EXTRACT(VALUE(le), '/OtherServiceDetails/@Quantity').getNUMBERval(),
                 decode(EXTRACT(VALUE(le), '/OtherServiceDetails/@Quantity')
                        .getnumberval(),
                        null,
                        1,
                        EXTRACT(VALUE(le), '/OtherServiceDetails/@Quantity')
                        .getnumberval()),
                 /* EXTRACT(VALUE(le), '/OtherServiceDetails/@PriorityID').getNUMBERval(), */
                 decode(EXTRACT(VALUE(le), '/OtherServiceDetails/@PriorityID')
                        .getnumberval(),
                        '0',
                        NULL,
                        EXTRACT(VALUE(le), '/OtherServiceDetails/@PriorityID')
                        .getnumberval()),
                 /* EXTRACT(VALUE(le), '/OtherServiceDetails/@ReferralDoctorID').getNUMBERval(), */
                 decode(EXTRACT(VALUE(le), '/OtherServiceDetails/@ReferralDoctorID')
                        .getnumberval(),
                        '0',
                        NULL,
                        EXTRACT(VALUE(le), '/OtherServiceDetails/@ReferralDoctorID')
                        .getnumberval()),
                 EXTRACT(VALUE(le), '/OtherServiceDetails/@ServiceItemID')
                 .getNUMBERval(),
                 TO_DATE(EXTRACT(VALUE(le), '/OtherServiceDetails/@StartDateTime')
                         .getSTRINGVAL(),
                         'DD-Mon-yyyy HH24:MI:SS'),
                 1,
                 /*EXTRACT(VALUE(le), '/OtherServiceDetails/@RequiredAt').getNUMBERval()*/
                 decode(EXTRACT(VALUE(le), '/OtherServiceDetails/@RequiredAt')
                        .getnumberval(),
                        '0',
                        NULL,
                        EXTRACT(VALUE(le), '/OtherServiceDetails/@RequiredAt')
                        .getnumberval()),
                 EXTRACT(VALUE(le), '/OtherServiceDetails/@AppointmentID')
                 .getNUMBERval()
            FROM TABLE(XMLSEQUENCE(EXTRACT(v_index, '/OtherServiceDetails'))) le;
      END IF;
      I := I + 1;
    END LOOP;
    OPEN OCURSOR_OTHERSERVICEDETAILS FOR
      SELECT OD.OTHERSERVICEDETAILID,
             OD.OTHERSERVICESREQUESTNO,
             OD.DEPTID,
             OD.PRIORITYID,
             OD.SERVICEITEMID SERVICEID,
             OD.STARTDATETIME,
             F_GETSTATUSMEANING(OD.REQUESTSTATUS,
                                'OTHERSERVICEDETAILS',
                                'REQUESTSTATUS') REQUESTSTATUS
        FROM OTHERSERVICEDETAILS OD
       WHERE OD.STATUS = 0
         AND OD.LOCATIONID = v_LocationId
         AND OD.OTHERSERVICESREQUESTNO = V_NEWREQUESTNO;
    /*AND OD.SERVICEITEMID IN (V_ARR)*/

  END IF;

  /*EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.put_line(SQLERRM);*/
END P_ADDOTHERSERVICESREQUEST;





