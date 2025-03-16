
  CREATE OR REPLACE  PROCEDURE "REGISTRATION"."GETPATIENTDETAILS_CLK" (IN_REGISTRATIONNUMBER IN PATIENT.UHID%TYPE,
                                                         in_LocationID      IN   NUMBER,
                                                         --For UHID Project
                                                         ocursor_Component1    OUT SYS_REFCURSOR,
                                                         --ocursor_Component2   OUT SYS_REFCURSOR,
                                                         ocursor_Component3  OUT SYS_REFCURSOR,
                                                         ocursor_Component4  OUT SYS_REFCURSOR,
                                                         ocursor_Component5  OUT SYS_REFCURSOR,
                                                         ocursor_Component6  OUT SYS_REFCURSOR,
                                                         ocursor_Component7  OUT SYS_REFCURSOR,
                                                         ocursor_Component8  OUT SYS_REFCURSOR,
                                                         ocursor_Component9  OUT SYS_REFCURSOR,
                                                         ocursor_Component10 OUT SYS_REFCURSOR,
                                                         ocursor_Component11 OUT SYS_REFCURSOR,
                                                         ocursor_Component12 OUT SYS_REFCURSOR,
                                                         ocursor_Component13 OUT SYS_REFCURSOR,
                                                         ocursor_Component14 OUT SYS_REFCURSOR,
                                                         ocursor_Component15 OUT SYS_REFCURSOR,
                                                        --For UHID Project(Please donot add new fields as input on top,as the existing services giving compilation error)
                                                         in_MasterFlag VARCHAR2 DEFAULT NULL
                                                         )
/*//////////////////////////////////////////////////////////////////////////////////
  //
  // File Description        :         p_getpatientdetailswithregno
  // Description             :         The purpose of this procedure is to get patientdetails
  // Parameters              :         in_UHID   INPUT
                                       in_PreregistrationNo   INPUT
                                       in_emergencyNo         INPUT
                                       ocursor_Component1   OUTPUT,
                                       ocursor_Component2   OUTPUT
                                       ocursor_Component3   OUTPUT
                                       ocursor_Component4   OUTPUT
                                       ocursor_Component5   OUTPUT
                                       ocursor_Component6   OUTPUT
                                       ocursor_Component7   OUTPUT
                                       ocursor_Component8   OUTPUT
                                       ocursor_Component9   OUTPUT
                                       ocursor_Component10   OUTPUT
                                       ocursor_Component11   OUTPUT
                                       ocursor_Component12   OUTPUT
                                       ocursor_Component13  OUTPUT
                                       ocursor_Component14   OUTPUT
                                       ocursor_Component15   OUTPUT
                                       ocursor_Component  OUTPUT
  // Returns                 :
  // ----------------------------------------------------------------------------------
  // Date Created            :         santosh challa
  // Author                  :
  // -----------------------------------------------------------------------------------
  // Change History          :
  // Date Modified           :          Month DD, YYYY (e.g. Sep 08, 2006)
  // Changed By              :
  // Change Description      :
  // Version                 :
  ////////////////////////////////////////////////////////////////////////////////////*/

 AS
  in_RegistrationID    varchar2(50);
  ln_RegistrationType  NUMBER(10);
  ln_genderLovID       NUMBER(10);
  ln_rhfactorLovID     NUMBER(10);
  ln_PRNExpiryDuration NUMBER(10);
  temp_type char(1);
  v_registrationnumber patient.uhid%type;
  --For UHID Testing
  --in_MasterFlag VARCHAR2(1):='Y';
  V_LOCALCOUNT         NUMBER := 0;
  V_MERGECOUNT         NUMBER := 0;
  V_PARENTUHID         patient.uhid%type;
BEGIN
  SELECT LOVID
    INTO ln_genderLovID
    FROM EHIS.Lovmaster
   WHERE UPPER(LOVCode) = 'GENDER';
SELECT LOVID
    INTO ln_rhfactorLovID
    FROM EHIS.Lovmaster
   WHERE UPPER(LOVCode) = 'RHFACTOR';

SELECT c.configuredvalue
    INTO ln_PRNExpiryDuration
    FROM EHIS.Configurationmaster c
   WHERE UPPER(c.configurationcode) = 'PRNEXPIRYDURATION';

temp_type:=UPPER(substr(IN_RegistrationNumber,1,1));
v_registrationnumber:=  TRIM(Upper(IN_RegistrationNumber));
BEGIN

--For UHID Project
IF in_MasterFlag = 'Y' THEN
      BEGIN
        SELECT RMU.PARENTUHID
          INTO V_PARENTUHID
          FROM REGISTRATION.MERGEDUHID RMU
         WHERE RMU.STATUS = 1
           AND RMU.MERGEDUHID = v_registrationnumber;

        V_MERGECOUNT := V_MERGECOUNT + 1;
      EXCEPTION
          WHEN NO_DATA_FOUND THEN
            BEGIN
              SELECT RMU.PARENTUHID
                INTO V_PARENTUHID
                FROM REGISTRATION.MERGEDUHID RMU
               WHERE RMU.STATUS = 1
                 AND RMU.PARENTUHID = v_registrationnumber
                 AND ROWNUM < 2;
              V_MERGECOUNT := V_MERGECOUNT + 1;
            EXCEPTION
              WHEN OTHERS THEN
                V_PARENTUHID := NULL;
                V_MERGECOUNT := 0;
            END;
          WHEN OTHERS THEN
            V_PARENTUHID := NULL;
            V_MERGECOUNT := 0;
      END;

      IF V_MERGECOUNT != 0 THEN
        SELECT COUNT(ROWID)
          INTO V_LOCALCOUNT
          FROM REGISTRATION.PATIENT P
         WHERE P.UHID = V_PARENTUHID;

        IF (V_LOCALCOUNT > 0) THEN
           SELECT P.REGISTRATIONID
             INTO IN_REGISTRATIONID
             FROM PATIENT P
            WHERE P.UHID = V_PARENTUHID;
        ELSE
           SELECT P.REGISTRATIONID
             INTO IN_REGISTRATIONID
             FROM MV_ENT_PATIENT_DETAILS P
            WHERE P.UHID = V_PARENTUHID;
        END IF;
      ELSE
       SELECT P.REGISTRATIONID, rm.RegistrationType
         INTO in_RegistrationID, ln_RegistrationType
         FROM Patient p
         LEFT OUTER JOIN RegistrationMaster rm
           ON p.registrationid = rm.registrationid
        WHERE P.STATUS = 1
          AND P.UHID = v_registrationnumber;
      END IF;
ELSE
  SELECT P.REGISTRATIONID, rm.RegistrationType
    INTO in_RegistrationID, ln_RegistrationType
    FROM Patient p
    LEFT OUTER JOIN RegistrationMaster rm
      ON p.registrationid = rm.registrationid
   WHERE P.STATUS = 1
     AND P.UHID = v_registrationnumber;
END IF;

EXCEPTION WHEN NO_DATA_FOUND THEN

BEGIN
IF (temp_type='A') THEN
  SELECT
  P.REGISTRATIONID, rm.RegistrationType
    INTO in_RegistrationID, ln_RegistrationType
    FROM Patient p
    LEFT OUTER JOIN RegistrationMaster rm ON p.registrationid = rm.registrationid
   WHERE (UHID = v_registrationnumber AND p.status = 1);
ELSIF (temp_type='E') THEN
  SELECT
  P.REGISTRATIONID, rm.RegistrationType
    INTO in_RegistrationID, ln_RegistrationType
    FROM Patient p
    LEFT OUTER JOIN RegistrationMaster rm ON p.registrationid = rm.registrationid
   WHERE (EmergencyNo = v_registrationnumber AND p.status = 1) ;
ELSIF (temp_type='P') THEN
  SELECT
  P.REGISTRATIONID, rm.RegistrationType
    INTO in_RegistrationID, ln_RegistrationType
    FROM Patient p
    LEFT OUTER JOIN RegistrationMaster rm ON p.registrationid = rm.registrationid
   WHERE (Preregistrationno = v_registrationnumber AND p.status = 1) ;

ELSE

  SELECT
  P.REGISTRATIONID, rm.RegistrationType
    INTO in_RegistrationID, ln_RegistrationType
    FROM Patient p
    LEFT OUTER JOIN RegistrationMaster rm ON p.registrationid = rm.registrationid
      WHERE (IN_RegistrationNumber IS NULL OR
         (UHID = v_registrationnumber OR
         Preregistrationno = v_registrationnumber OR
         EmergencyNo = v_registrationnumber) AND p.status = 1) ;

END IF;

         EXCEPTION WHEN OTHERS THEN
      DBMS_OUTPUT.PUT_LINE(TO_CHAR(SQLCODE) || SQLERRM);
END;
      WHEN OTHERS THEN
      DBMS_OUTPUT.PUT_LINE(TO_CHAR(SQLCODE) || SQLERRM);

END;
  --abc := in_RegistrationID;
  --AND  (IN_RegistrationNumber is null OR Upper(Preregistrationno)=Upper(IN_RegistrationNumber));
  /*AND (IN_RegistrationNumber is null OR Upper(EmergencyNo)=Upper(IN_RegistrationNumber))
  */

IF (IN_MASTERFLAG = 'Y' AND V_MERGECOUNT != 0 AND V_LOCALCOUNT = 0) THEN
  OPEN ocursor_Component1 FOR
    SELECT RegistrationID,
           PreRegistrationNo,
           NULL AS  EmergencyNo,
           UHID,
           (SELECT RegistrationType
              FROM registrationmaster
             WHERE Registrationid = in_RegistrationID) RegistrationType,
           LocationID,
           NULL AS  CorporateEmployeeID,
           NULL AS  CorporateID,
           NULL AS  RefferalDoctorID,
           NULL AS  RefferalEntityID,
           NULL AS  EmployeeID,
           NULL AS  RecruitmentID,
           NULL AS  EmployeeReferralID,
           NULL AS  RelationshipCode,
           NULL AS  CampID,
           NULL AS  CampName,
           NULL AS  CampType,
           NULL AS  CampRegistrationID,
           NULL AS  BatchID,
           NULL AS  Babyof,
           NULL AS MOTHERSUHID,
           title,
           TM.TITLETYPE,
           (CASE
              WHEN (p.flag = 2 AND p.regularizationcheck = 0) THEN
               'QuickRegistration'

              WHEN (p.flag = 2 AND p.regularizationcheck = 1) THEN
               'Regularized'
              WHEN (p.flag = 27 AND p.regularizationcheck = 1) THEN
               'RegularizedEMY'
              ELSE
               'Registration'
            END) as regularizationcheck,


           (CASE
             WHEN UPPER(PM.PRIVACYTYPE) = 'VERY HIGH' THEN
              P.ALIASNAME
             ELSE
              P.FirstName
           END) AS FirstName,
           MiddleName,
           (CASE
             WHEN UPPER(PM.PRIVACYTYPE) = 'VERY HIGH' THEN
              ''
             ELSE
              P.LastName
           END) AS LastName,
           TM.TITLETYPE || ' ' || FirstName || ' ' || ' ' || MiddleName || ' ' ||
           LastName || ' ' || SM.SUFFIXNAME AS PatientName,
           Sufix,
           SM.SUFFIXNAME SuffixName,
           NULL AS EducationalQualification,
           NULL AS OtherDegree,
           to_char(BirthDate, 'DD-MON-YYYY') BirthDate,
           NULL AS  BirthTime,
           FatherName,
           SpouseName,
           MotherMaidenName,
           GaurdianName,
           NULL AS Birthplace,
           NULL AS Approximate,
            floor(months_between(SYSDATE, BirthDate)/12) ||' -Yrs '|| floor( mod(months_between(sysdate, BirthDate),12))||' -Months' as Age,
           NULL AS AgeType,
           NULL AS Agecategory,
           Gender,
           LD.LOVDETAILVALUE GenderType,
           MARITALSTATUS,
           MSM.MARITALSTATUSTYPE,
           NULL AS Religion,
           NULL AS Race,
           NULL AS Ethnicgroup,
           NULL AS Employmentstatus,
           NULL AS Monthlyincome,
           NULL AS PrimaryLanguage,
           NULL AS TranslatorRequired,
           NULL AS TranslatorName,
           Citizenship,
           NULL AS Literate,
           NULL AS FinancialStatus,
           NULL AS EmotionalBarriers,
           PatientType,

           NULL AS Disability,
           NULL AS DisabledPersonCode,
           NULL AS DisabledPersonIdentifier,
           NULL AS IdentificationMark1,
           NULL AS IdentificationMark2,
           NULL AS Socialsecuritynumber,
           PossessPassport,
           NULL AS Diabetic,
           Allergic,
           BLOODGROUP,
           BGM.BLOODGROUPNAME,
           Rhfactor,
           rf.lovdetailvalue RHFactorName,
           NULL AS Donor,
           NULL AS DonorType,
           NULL AS OrganType,
           NULL AS DonorCode,
           NULL AS PaymentForRegistration,
           NULL AS PaymentCurrency,
           NULL AS BillingTypeID,
           NULL AS ReferenceNo,
           CreatedBy,
           CreatedDate,
           NULL AS HowDoYouComeToKnowAboutUs,
           NULL AS PreferredModeOfContact,
           NULL AS WantAlertsOnHospitalPromotions,
           NULL AS FileName,
           NULL AS FileType,
           NULL AS FilePath,
           p.Status,
           NULL AS EmailID,
           NULL AS Business,
           NULL AS PreferredLocation,
           PrivacyStatus,
           CustomerStatus,
           (SELECT L.LOVDETAILID FROM ehis.lovdetail L WHERE upper(L.LOVDETAILVALUE)=upper(CustomerStatus)) AS CustomerStatusID ,
           p.AliasName,
           NULL AS StartDate,
           NULL AS EndDate,
           NoOfIssues,
           (CASE
             WHEN (((p.createddate + ln_PRNExpiryDuration) < SYSDATE) AND
                  (p.preregistrationno IS NOT NULL OR
                  p.preregistrationno <> '')) THEN
              'Expired'
             ELSE
              ''
           END) PRNStatus,
           p.UpdatedBy,
           p.UpdatedDate,
           p.Status,
           NULL AS Draft,
           NULL AS TempDraftID,
           NULL AS IsMlccase,
           NULL AS MlcCaseNo,
           NULL AS IsHyperTension,
           NULL AS havecommunicabledisease,
           NULL AS patientpreference,
           NULL AS foodpreference,
           NULL AS diabetictype,
           NULL AS deathdatetime,
           NULL AS EmployeeRelation,
           NULL AS EventID,
           NULL AS EventName,
           NULL AS EventType,
           P.FIRSTNAME AS FirstName1,
           P.LastName AS LastName1,
           NULL AS ReferralPatientUHID,
             p.flag as flag,
           p.regularizationcheck As regularization,
           NULL AS Emergencyflag,
           'Y' ENTERPRISEFLAG,
           ERM.REGIONNAME

      FROM MV_ENT_PATIENT_DETAILS p
      LEFT OUTER JOIN EHIS.Titlemaster TM ON p.title = tm.titlecode
      LEFT OUTER JOIN EHIS.SuffixMaster SM on p.sufix = SM.SUFFIXCODE
      LEFT OUTER JOIN EHIS.Maritalstatusmaster MSM ON MSM.MARITALSTATUSID = p.maritalstatus
      LEFT OUTER JOIN EHIS.Bloodgroupmaster BGM ON BGM.BLOODGROUPID = p.bloodgroup
      LEFT OUTER JOIN EHIS.LovDetail LD ON(LD.LOVDETAILID = p.gender AND LD.LOVID = ln_genderLovID)
      LEFT OUTER JOIN EHIS.LovDetail rf ON(rf.LOVDETAILID = p.rhfactor AND rf.LOVID = ln_rhfactorLovID)
      LEFT OUTER JOIN EHIS.PRIVACYMASTER PM ON P.PRIVACYSTATUS = PM.PRIVACYID
      JOIN EHIS.REGIONMAPPINGMASTER RMM
        ON ROWNUM = 1
       AND RMM.STATUS = 1
       AND RMM.CHARTID = P.LOCATIONID
      JOIN EHIS.REGIONMASTER ERM
        ON ERM.STATUS = 1
       AND ERM.REGIONID = RMM.REGIONID
     WHERE p.Status = 1
       AND RegistrationID = in_RegistrationID;
ELSE
  OPEN ocursor_Component1 FOR
    SELECT RegistrationID,
           PreRegistrationNo,
           EmergencyNo,
           UHID,
           (SELECT RegistrationType
              FROM registrationmaster
             WHERE Registrationid = in_RegistrationID) RegistrationType,
           LocationID,
           CorporateEmployeeID,
           CorporateID,
           RefferalDoctorID,
           RefferalEntityID,
           EmployeeID,
           RecruitmentID,
           EmployeeReferralID,
           RelationshipCode,
           CampID,
           CampName,
           CampType,
           CampRegistrationID,
           BatchID,
           Babyof,
           P.MOTHERSUHID,
           title,
           TM.TITLETYPE,
              (case
             when (p.reasonforfree = 'Quick Registration' and
                  p.regularizationcheck = 0) then
              'NOTREGULARIZED'

             when (p.reasonforfree = 'Quick Registration' and
                  p.regularizationcheck = 1) then
              'REGULARIZED'
             else
              'Registration'
           end) as regularizationcheck,


           (CASE
             WHEN UPPER(PM.PRIVACYTYPE) = 'VERY HIGH' THEN
              P.ALIASNAME
             ELSE
              P.FirstName
           END) AS FirstName,
           MiddleName,
           (CASE
             WHEN UPPER(PM.PRIVACYTYPE) = 'VERY HIGH' THEN
              ''
             ELSE
              P.LastName
           END) AS LastName,
           TM.TITLETYPE || ' ' || FirstName || ' ' || ' ' || MiddleName || ' ' ||
           LastName || ' ' || SM.SUFFIXNAME AS PatientName,
           Sufix,
           SM.SUFFIXNAME SuffixName,
           EducationalQualification,
           OtherDegree,
           to_char(BirthDate, 'DD-MON-YYYY') BirthDate,
           to_char(BirthTime, 'DD-MON-YYYY HH24:MI:SS') BirthTime,
           FatherName,
           SpouseName,
           MotherMaidenName,
           GaurdianName,
           Birthplace,
           Approximate,
            floor(months_between(SYSDATE, BirthDate)/12) ||' -Yrs '|| floor( mod(months_between(sysdate, BirthDate),12))||' -Months' as Age,
           AgeType,
           Agecategory,
           Gender,
           LD.LOVDETAILVALUE GenderType,
           MARITALSTATUS,
           MSM.MARITALSTATUSTYPE,
           Religion,
           Race,
           Ethnicgroup,
           Employmentstatus,
           Monthlyincome,
           PrimaryLanguage,
           TranslatorRequired,
           TranslatorName,
           Citizenship,
           Literate,
           FinancialStatus,
           EmotionalBarriers,
           PatientType,

           Disability,
           DisabledPersonCode,
           DisabledPersonIdentifier,
           IdentificationMark1,
           IdentificationMark2,
           Socialsecuritynumber,
           PossessPassport,
           Diabetic,
           Allergic,
           BLOODGROUP,
           BGM.BLOODGROUPNAME,
           Rhfactor,
           rf.lovdetailvalue RHFactorName,
           Donor,
           DonorType,
           OrganType,
           DonorCode,
           PaymentForRegistration,
           PaymentCurrency,
           PaymentMethod BillingTypeID,
           ReferenceNo,
           CreatedBy,
           CreatedDate,
           HowDoYouComeToKnowAboutUs,
           PreferredModeOfContact,
           WantAlertsOnHospitalPromotions,
           FileName,
           FileType,
           FilePath,
           p.Status,
           EmailID,
           Business,
           PreferredLocation,
           PrivacyStatus,
           CustomerStatus,
           (SELECT L.LOVDETAILID FROM ehis.lovdetail L WHERE upper(L.LOVDETAILVALUE)=upper(CustomerStatus)) AS CustomerStatusID ,
           p.AliasName,
           StartDate,
           EndDate,
           NoOfIssues,
           (CASE
             WHEN (((p.createddate + ln_PRNExpiryDuration) < SYSDATE) AND
                  (p.preregistrationno IS NOT NULL OR
                  p.preregistrationno <> '')) THEN
              'Expired'
             ELSE
              ''
           END) PRNStatus,
           p.UpdatedBy,
           p.UpdatedDate,
           p.Status,
           Draft,
           TempDraftID,
           IsMlccase,
           MlcCaseNo,
           IsHyperTension,
           havecommunicabledisease,
           patientpreference,
           foodpreference,
           diabetictype,
           TO_CHAR(deathdatetime, 'DD-MON-YYYY HH24:MI:SS') AS deathdatetime,
           EmployeeRelation,
           EventID,
           EventName,
           EventType,
           P.FIRSTNAME AS FirstName1,
           P.LastName AS LastName1,
           ReferralPatientUHID,
             p.flag as flag,
           p.regularizationcheck As regularization,
           P.Emergencyflag,
           NULL AS ENTERPRISEFLAG,
           NULL AS REGIONNAME

      FROM PATIENT p
      LEFT OUTER JOIN EHIS.Titlemaster TM ON p.title = tm.titlecode
      LEFT OUTER JOIN EHIS.SuffixMaster SM on p.sufix = SM.SUFFIXCODE
      LEFT OUTER JOIN EHIS.Maritalstatusmaster MSM ON MSM.MARITALSTATUSID = p.maritalstatus
      LEFT OUTER JOIN EHIS.Bloodgroupmaster BGM ON BGM.BLOODGROUPID = p.bloodgroup
      LEFT OUTER JOIN EHIS.LovDetail LD ON(LD.LOVDETAILID = p.gender AND LD.LOVID = ln_genderLovID)
      LEFT OUTER JOIN EHIS.LovDetail rf ON(rf.LOVDETAILID = p.rhfactor AND rf.LOVID = ln_rhfactorLovID)
      LEFT OUTER JOIN EHIS.PRIVACYMASTER PM ON P.PRIVACYSTATUS = PM.PRIVACYID
     WHERE RegistrationID = in_RegistrationID AND
           ((p.Status = 1 OR p.draft = 1) );

END IF;
  /*  COMMIT;*/
  /*OPEN ocursor_Component2
  FOR

  SELECT RegistrationID,ResidenceNumber,MobileNumber,PrimaryEmail,Country,State,District,City,Address1,Address2,Pincode
  FROM AddressMaster
  WHERE UPPER(RegistrationID)=UPPER(in_RegistrationID) AND Status=1
  AND AddressTypeID=(SELECT AddressTypeID FROM AddressTypeMaster
  WHERE AddressTypeName='PermanentAddress');*/

  OPEN ocursor_Component3 FOR

    SELECT RegistrationID,
           ResidenceNumber,
           MobileNumber,
           PrimaryEmail,
           Country,
           State,
           District,
           City,
           Address1,
           Address2,
           Pincode
      FROM AddressMaster amr
     WHERE RegistrationID = in_RegistrationID AND amr.Status = 1 AND
           AddressTypeID =
           (SELECT AddressTypeID
              FROM AddressTypeMaster
             WHERE AddressTypeName = 'PERMANENTADDRESS');
  /*  COMMIT;*/

  OPEN ocursor_Component4 FOR

    SELECT ResidenceNumber,
           MobileNumber,
           EmergencyNumber,
           PrimaryEmail,
           Country,
           CM.COUNTRYTYPE,
           State,
           sm.statename,
           District,
           dm.districtname,
           City,
           cm1.cityname,
           Address1,
           Address2,
           Pincode
      FROM AddressMaster am LEFT OUTER JOIN EHIS.Countrymaster CM ON CM.COUNTRYID = am.country LEFT OUTER JOIN EHIS.Statemaster SM ON SM.STATEID = am.state AND SM.COUNTRYID=AM.COUNTRY LEFT OUTER JOIN EHIS.Districtmaster DM ON DM.DISTRICTID = am.district AND DM.STATEID=AM.STATE LEFT OUTER JOIN EHIS.Citymaster CM1 ON CM1.CITYID = am.city AND CM1.DISTRICTID=AM.DISTRICT
     WHERE RegistrationID = in_RegistrationID AND am.Status = 1 AND
           AddressTypeID =
           (SELECT AddressTypeID
              FROM AddressTypeMaster
             WHERE AddressTypeName = 'CURRENTADDRESS');
  /*  COMMIT;*/

  OPEN ocursor_Component5 FOR

    SELECT OrganizationName,
           EmployeeNumber,
           Country,
           State,
           District,
           City,
           Address1,
           Address2,
           Pincode,
           PrimaryEmail,
           AlternateEmail,
           OfficeNumber,
           Extension,
           ResidenceNumber,
           MobileNumber,
           EmergencyNumber,
           OfficeFaxNumber,
           ResidenceFaxNumber
      FROM PatientWorkplaceDetail PWD INNER JOIN AddressMaster AM ON PWD.RegistrationID = AM.RegistrationID
     WHERE PWD.RegistrationID = in_RegistrationID AND PWD.Status = 1 AND
           AddressTypeID =
           (SELECT AddressTypeID
              FROM AddressTypeMaster
             WHERE AddressTypeName = 'PATIENTWORKPLACEDETAIL');
  /*  COMMIT;*/

  OPEN ocursor_Component6 FOR

    SELECT ContactPersonName,
           Gender,
           TO_CHAR(BirthDate, 'DD-MON-YYYY') AS BirthDate,
           Citizenship,
           Primarylanguage,
           Nationality,
           PassportNumber,
           SocialSecuritynumber,
           Relationship,
           Country,
           State,
           District,
           City,
           Address1,
           Address2,
           Pincode,
           ResidenceNumber,
           OfficeNumber,
           MobileNumber,
           PrimaryEmail
      FROM ContactPersonDetail CPD LEFT OUTER JOIN AddressMaster AM ON CPD.RegistrationID = AM.RegistrationID
     WHERE CPD.RegistrationID = in_RegistrationID AND CPD.Status = 1 AND
           AddressTypeID =
           (SELECT AddressTypeID
              FROM AddressTypeMaster
             WHERE AddressTypeName = 'EMERGENCYADDRESS');
  /*  COMMIT;*/

  OPEN ocursor_Component7 FOR

    SELECT p.REFFERALDOCTORID

      FROM Patient p

     WHERE RegistrationID = in_RegistrationID;

  /*  COMMIT;*/

  OPEN ocursor_Component8 FOR

    SELECT p.REFFERALENTITYID
      FROM PATIENT p
     WHERE RegistrationID = in_RegistrationID;
  /*  COMMIT;*/

  OPEN ocursor_Component9 FOR

    SELECT habit
      FROM PatientHabit
     WHERE RegistrationID = in_RegistrationID;
  /*  COMMIT;*/

  OPEN ocursor_Component10 FOR

    SELECT HealthPlanTypeID,
           HealthPlanType HealthPlanTypeName,
           InsurerID,
           InsurerName,
           TPAID,
           TPAName,
           CorporateID,
           CorporateName,
           PolicyID POLICYID,
           PolicyID POLICYNAME,
           PrimaryPayerid AS PrimaryPayerID,
           PayerName AS PrimaryPayerName,
           to_char(ID.IssueDate, 'DD-MON-YYYY') IssueDate,
           to_char(ID.ExpiryDate, 'DD-MON-YYYY') ExpiryDate,
           ID.PolicyNo,
           ID.EmployeeIDNo,
           ID.SubscriberName,
           RM.RELATIONSHIPTYPE SubscriberRelationship,
           ID.SubscriberRelationship SubscriberRelationshipID,
           to_char(ID.ExpiryDate, 'dd/mm/yyyy'),
           ID.SubscriberDesignation,
           ID.SubscriberEmail,
           ID.SubscriberCardType,
           ID.SubscriberColor,
           Preference,
           Aggrement,
           AG.AGREEMENTNAME
      FROM InsuranceDetails ID LEFT OUTER JOIN EHIS.RelationshipMaster RM on ID.Subscriberrelationship = RM.RELATIONSHIPCODE LEFT OUTER JOIN AGREEMENTS AG ON ID.AGGREMENT = AG.AGREEMENTID
     WHERE ID.RegistrationID = in_RegistrationID AND ID.STATUS = 1 AND
           to_date(ID.ExpiryDate) > SYSDATE;

  /*  COMMIT;*/

 OPEN OCURSOR_COMPONENT11 FOR
   SELECT LD.ALLERGYTYPEID        AS ALLERGENTYPEID,
           LD.ALLERGYTYPENAME      AS ALLERGENTYPE,
           ASM.ALLERGYSEVERITYID AS ALLERGENSEVERITYID,
           ASM.ALLERGYSEVERITYNAME AS ALLERGYSEVERITY,
           NVL(AM.ALLERGENID, AGM.GROUPID) AS ALLERGENID,
           NVL(NVL(AM.ALLERGENNAME, AGM.GROUPNAME), PA.ALLERGEN_NAME) AS ALLERGEN,
           PA.ALLERGYDESC AS ALLERGYDESCRIPTIONID,
           NVL2(PA.GROUPID, '1', '0') ISGROUP,
           pa.status,
           PA.Patientallergy_Id,
           ASM.SEVERITYTOOLTIP AS TOOLTIP,
           ASM.OVERRIDE,
           AM.GENERICNAME AS GENERICNAME,
           PA.INACTIVATEREASON,
           PA.INACTIVATEDATE,
            TO_CHAR(PA.createddate, 'MM/DD/YYYY HH:MI:SS AM') as createddate,
            null as FLAG1,
              CASE
                   WHEN PA.STATUS = 2 OR PA.STATUS = 6  THEN 1
                   else  0
                   END AS "SORTSTATUS"
      FROM REGISTRATION.PATIENTALLERGY PA
      LEFT OUTER JOIN EHIS.ALLERGYTYPEMASTER LD
        ON PA.ALLERGENTYPE = LD.ALLERGYTYPEID
      LEFT OUTER JOIN EHIS.EH_AY_SEVERITY_MASTER_MV ASM
        ON PA.ALLERGYSEVERITY = ASM.ALLERGYSEVERITYID
      LEFT OUTER JOIN EHIS.Eh_Ay_Master_Mv AM
        ON PA.ALLERGEN = AM.ALLERGENID
      LEFT OUTER JOIN EHIS.EH_AY_SETMASTER_MV AGM
        ON PA.GROUPID = AGM.GROUPID

    WHERE
  PA.STATUS  <> 0
     and PA.STATUS = 1

       AND PA.REGISTRATIONID = IN_REGISTRATIONID
       order by SORTSTATUS;
  /*  COMMIT;*/

  OPEN ocursor_Component12 FOR
    SELECT p.CORPORATEID
      FROM Patient p
     WHERE RegistrationID = in_RegistrationID;

  /*  COMMIT;*/

  OPEN ocursor_Component13 FOR

    SELECT Nationality,
           InternationalPatient,
           CountryIssued,
           PassportNumber,
           TO_CHAR(PassportIssuedate, 'DD-MON-YYYY') AS PassportIssuedate,
           TO_CHAR(PassportExpirydate, 'DD-MON-YYYY') AS PassportExpirydate,
           VisaType,
           VisaIssuingAuthority,
           TO_CHAR(VisaIssueDate, 'DD-MON-YYYY') AS VisaIssueDate,
           TO_CHAR(VisaExpiryDate, 'DD-MON-YYYY') AS VisaExpiryDate,
           StartDate,
           EndDate
      FROM Registration.PatientVisaDetail
     WHERE RegistrationID = in_RegistrationID AND Status = 1;
  /*  COMMIT;*/

  OPEN ocursor_Component14 FOR
    SELECT PatientFileType, PatientFileName, PatientFilePath
      FROM PatientExternalMedicalRecords
     WHERE RegistrationID = in_RegistrationID AND Status = 1;
  /*  COMMIT;*/

  OPEN ocursor_Component15 FOR

    SELECT EmailID, UserID, HintQuestion, HintAnswer
      FROM LoginDetails
     WHERE RegistrationID = in_RegistrationID;

  /*Open ocursor_Component16 FOR

    select LINKEDUHID
      from REGISTRATION.LINKEDUHID
     WHERE ParentUHID = in_UHID and Status = 1;

  OPEN ocursor_Component17 FOR
    select MERGEDUHID
      from REGISTRATION.MERGEDUHID
     WHERE ParentUHID = in_UHID and Status = 1;*/

  /*
    COMMIT;
  EXCEPTION

    WHEN OTHERS THEN
      DBMS_OUTPUT.PUT_LINE(TO_CHAR(SQLCODE) || SQLERRM);*/

END GETPATIENTDETAILS_CLK;

