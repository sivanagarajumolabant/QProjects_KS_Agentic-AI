
CREATE OR REPLACE PROCEDURE REGISTRATION.GETPATIENTDETAILS_CLK(IN_REGISTRATIONNUMBER IN REGISTRATION.PATIENT.UHID%TYPE,
in_LocationID IN numeric,
--For UHID Project


ocursor_Component1 inout refcursor,
--ocursor_Component2 OUT SYS_REFCURSOR,


ocursor_Component3 inout refcursor,
ocursor_Component4 inout refcursor,
ocursor_Component5 inout refcursor,
ocursor_Component6 inout refcursor,
ocursor_Component7 inout refcursor,
ocursor_Component8 inout refcursor,
ocursor_Component9 inout refcursor,
ocursor_Component10 inout refcursor,
ocursor_Component11 inout refcursor,
ocursor_Component12 inout refcursor,
ocursor_Component13 inout refcursor,
ocursor_Component14 inout refcursor,
ocursor_Component15 inout refcursor,
--For UHID Project(Please donot add new fields as input on top,as the existing services giving compilation error)


in_MasterFlag varchar default null
)
/*
//////////////////////////////////////////////////////////////////////////////////
 //
 // File Description : p_getpatientdetailswithregno
 // Description : The purpose of this procedure is to get patientdetails
 // Parameters : in_UHID INPUT
 in_PreregistrationNo INPUT
 in_emergencyNo INPUT
 ocursor_Component1 OUTPUT,
 ocursor_Component2 OUTPUT
 ocursor_Component3 OUTPUT
 ocursor_Component4 OUTPUT
 ocursor_Component5 OUTPUT
 ocursor_Component6 OUTPUT
 ocursor_Component7 OUTPUT
 ocursor_Component8 OUTPUT
 ocursor_Component9 OUTPUT
 ocursor_Component10 OUTPUT
 ocursor_Component11 OUTPUT
 ocursor_Component12 OUTPUT
 ocursor_Component13 OUTPUT
 ocursor_Component14 OUTPUT
 ocursor_Component15 OUTPUT
 ocursor_Component OUTPUT
 // Returns :
 // 
 // Date Created : santosh challa
 // Author :
 // 
 // Change History :
 // Date Modified : Month DD, YYYY (e.g. Sep 08, 2006)
 // Changed By :
 // Change Description :
 // Version :
 ////////////////////////////////////////////////////////////////////////////////////
*/


language plpgsql
 as $BODY$
declare
in_RegistrationID varchar(50);
ln_RegistrationType numeric(10);
ln_genderLovID numeric(10);
ln_rhfactorLovID numeric(10);
ln_PRNExpiryDuration numeric(10);
temp_type char(1);
v_registrationnumber REGISTRATION.PATIENT.UHID%TYPE;
--For UHID Testing


--in_MasterFlag VARCHAR2(1):='Y';


V_LOCALCOUNT numeric := 0;
V_MERGECOUNT numeric := 0;
V_PARENTUHID REGISTRATION.PATIENT.UHID%TYPE;
begin
set search_path to REGISTRATION;
SELECT LOVID
into strict ln_genderLovID
FROM EHIS.Lovmaster
WHERE UPPER(LOVCode)= 'GENDER';
SELECT LOVID
into strict ln_rhfactorLovID
FROM EHIS.Lovmaster
WHERE UPPER(LOVCode)= 'RHFACTOR';
SELECT c.configuredvalue
into strict ln_PRNExpiryDuration
FROM EHIS.Configurationmaster c
WHERE UPPER(c.configurationcode)= 'PRNEXPIRYDURATION';
temp_type:= UPPER(substr(IN_RegistrationNumber,1,1));
v_registrationnumber:= TRIM(Upper(IN_RegistrationNumber));
BEGIN
--For UHID Project


IF in_MasterFlag = 'Y' THEN
BEGIN
SELECT RMU.PARENTUHID
into strict V_PARENTUHID
FROM REGISTRATION.MERGEDUHID RMU
WHERE RMU.STATUS = 1
AND RMU.MERGEDUHID = v_registrationnumber;
V_MERGECOUNT := V_MERGECOUNT + 1;
EXCEPTION
WHEN NO_DATA_FOUND THEN
BEGIN
SELECT RMU.PARENTUHID
into strict V_PARENTUHID
FROM REGISTRATION.MERGEDUHID RMU
WHERE RMU.STATUS = 1
AND RMU.PARENTUHID = v_registrationnumber
limit 1;
V_MERGECOUNT := V_MERGECOUNT + 1;
EXCEPTION
WHEN OTHERS THEN
V_PARENTUHID DEFAULTnull;
V_MERGECOUNT := 0;
END;
WHEN OTHERS THEN
V_PARENTUHID DEFAULTnull;
V_MERGECOUNT := 0;
END;
IF V_MERGECOUNT != 0 THEN
SELECT COUNT(ctid)
into strict V_LOCALCOUNT
FROM REGISTRATION.PATIENT P
WHERE P.UHID = V_PARENTUHID;
IF(V_LOCALCOUNT > 0)THEN
SELECT P.REGISTRATIONID
into strict IN_REGISTRATIONID
from REGISTRATION.PATIENT P
WHERE P.UHID = V_PARENTUHID;
ELSE
SELECT P.REGISTRATIONID
into strict IN_REGISTRATIONID
from REGISTRATION.MV_ENT_PATIENT_DETAILS P
WHERE P.UHID = V_PARENTUHID;
END IF;
ELSE
SELECT P.REGISTRATIONID, rm.RegistrationType
into strict in_RegistrationID, ln_RegistrationType
FROM Patient p
LEFT OUTER JOIN REGISTRATION.RegistrationMaster rm
ON p.registrationid = rm.registrationid
WHERE P.STATUS = 1
AND P.UHID = v_registrationnumber;
END IF;
ELSE
SELECT P.REGISTRATIONID, rm.RegistrationType
into strict in_RegistrationID, ln_RegistrationType
FROM Patient p
LEFT OUTER JOIN REGISTRATION.RegistrationMaster rm
ON p.registrationid = rm.registrationid
WHERE P.STATUS = 1
AND P.UHID = v_registrationnumber;
END IF;
EXCEPTION WHEN NO_DATA_FOUND THEN
BEGIN
IF(temp_type = 'A')THEN
SELECT
P.REGISTRATIONID, rm.RegistrationType
into strict in_RegistrationID, ln_RegistrationType
FROM Patient p
LEFT OUTER JOIN REGISTRATION.RegistrationMaster rm ON p.registrationid = rm.registrationid
WHERE(UHID = v_registrationnumber AND p.status = 1);
ELSIF(temp_type = 'E')THEN
SELECT
P.REGISTRATIONID, rm.RegistrationType
into strict in_RegistrationID, ln_RegistrationType
FROM Patient p
LEFT OUTER JOIN REGISTRATION.RegistrationMaster rm ON p.registrationid = rm.registrationid
WHERE(EmergencyNo = v_registrationnumber AND p.status = 1);
ELSIF(temp_type = 'P')THEN
SELECT
P.REGISTRATIONID, rm.RegistrationType
into strict in_RegistrationID, ln_RegistrationType
FROM Patient p
LEFT OUTER JOIN REGISTRATION.RegistrationMaster rm ON p.registrationid = rm.registrationid
WHERE(Preregistrationno = v_registrationnumber AND p.status = 1);
ELSE
SELECT
P.REGISTRATIONID, rm.RegistrationType
into strict in_RegistrationID, ln_RegistrationType
FROM Patient p
LEFT OUTER JOIN REGISTRATION.RegistrationMaster rm ON p.registrationid = rm.registrationid
WHERE(IN_RegistrationNumber
is NULL OR(UHID = v_registrationnumber OR
Preregistrationno = v_registrationnumber OR
EmergencyNo = v_registrationnumber)AND p.status = 1);
END IF;
EXCEPTION WHEN OTHERS THEN
raise notice '% % ',TO_CHARSQLCODE, SQLERRM;
END;
WHEN OTHERS THEN
raise notice '% % ',TO_CHARSQLCODE, SQLERRM;
END;
--abc := in_RegistrationID;


--AND (IN_RegistrationNumber is null OR Upper(Preregistrationno)=Upper(IN_RegistrationNumber));


/*
AND (IN_RegistrationNumber is null OR Upper(EmergencyNo)=Upper(IN_RegistrationNumber))
 
*/

IF(IN_MASTERFLAG = 'Y' AND V_MERGECOUNT != 0 AND V_LOCALCOUNT = 0)THEN
OPEN ocursor_Component1 FOR
SELECT RegistrationID,
PreRegistrationNo,
NULL
as EmergencyNo,
UHID,(SELECT RegistrationType
from REGISTRATION.registrationmaster
WHERE Registrationid = in_RegistrationID::numeric)RegistrationType,
LocationID,
NULL
as CorporateEmployeeID,
NULL
as CorporateID,
NULL
as RefferalDoctorID,
NULL
as RefferalEntityID,
NULL
as EmployeeID,
NULL
as RecruitmentID,
NULL
as EmployeeReferralID,
NULL
as RelationshipCode,
NULL
as CampID,
NULL
as CampName,
NULL
as CampType,
NULL
as CampRegistrationID,
NULL
as BatchID,
NULL
as Babyof,
NULL
as MOTHERSUHID,
title,
TM.TITLETYPE,(CASE
WHEN(p.flag = 2 AND p.regularizationcheck = 0)THEN
'QuickRegistration'
WHEN(p.flag = 2 AND p.regularizationcheck = 1)THEN
'Regularized'
WHEN(p.flag = 27 AND p.regularizationcheck = 1)THEN
'RegularizedEMY'
ELSE
'Registration'
END)
as regularizationcheck,(CASE
WHEN UPPER(PM.PRIVACYTYPE)= 'VERY HIGH' THEN
P.ALIASNAME
ELSE
P.FirstName
END)
as FirstName,
MiddleName,(CASE
WHEN UPPER(PM.PRIVACYTYPE)= 'VERY HIGH' THEN
''
ELSE
P.LastName
END)
as LastName,
TM.TITLETYPE || ' ' || FirstName || ' ' || ' ' || MiddleName || ' ' ||
LastName || ' ' || SM.SUFFIXNAME
as PatientName,
Sufix,
SM.SUFFIXNAME SuffixName,
NULL
as EducationalQualification,
NULL
as OtherDegree,
to_char(BirthDate, 'DD - MON - YYYY')BirthDate,
NULL
as BirthTime,
FatherName,
SpouseName,
MotherMaidenName,
GaurdianName,
NULL
as Birthplace,
NULL
as Approximate,
floor(oracle.months_between(current_timestamp(0)::timestamp, BirthDate)/12)||' - Yrs '|| floor(mod(oracle.months_between(current_timestamp(0)::timestamp, BirthDate),12))||' - Months'
as Age,
NULL
as AgeType,
NULL
as Agecategory,
Gender,
LD.LOVDETAILVALUE GenderType,
MARITALSTATUS,
MSM.MARITALSTATUSTYPE,
NULL
as Religion,
NULL
as Race,
NULL
as Ethnicgroup,
NULL
as Employmentstatus,
NULL
as Monthlyincome,
NULL
as PrimaryLanguage,
NULL
as TranslatorRequired,
NULL
as TranslatorName,
Citizenship,
NULL
as Literate,
NULL
as FinancialStatus,
NULL
as EmotionalBarriers,
PatientType,
NULL
as Disability,
NULL
as DisabledPersonCode,
NULL
as DisabledPersonIdentifier,
NULL
as IdentificationMark1,
NULL
as IdentificationMark2,
NULL
as Socialsecuritynumber,
PossessPassport,
NULL
as Diabetic,
Allergic,
BLOODGROUP,
BGM.BLOODGROUPNAME,
Rhfactor,
rf.lovdetailvalue RHFactorName,
NULL
as Donor,
NULL
as DonorType,
NULL
as OrganType,
NULL
as DonorCode,
NULL
as PaymentForRegistration,
NULL
as PaymentCurrency,
NULL
as BillingTypeID,
NULL
as ReferenceNo,
CreatedBy,
CreatedDate,
NULL
as HowDoYouComeToKnowAboutUs,
NULL
as PreferredModeOfContact,
NULL
as WantAlertsOnHospitalPromotions,
NULL
as FileName,
NULL
as FileType,
NULL
as FilePath,
p.Status,
NULL
as EmailID,
NULL
as Business,
NULL
as PreferredLocation,
PrivacyStatus,
CustomerStatus,(SELECT L.LOVDETAILID FROM ehis.lovdetail L WHERE upper(L.LOVDETAILVALUE)= upper(CustomerStatus))
as CustomerStatusID ,
p.AliasName,
NULL
as StartDate,
NULL
as EndDate,
NoOfIssues,(CASE
WHEN(((p.createddate + ln_PRNExpiryDuration)< current_timestamp(0)::timestamp)AND(p.preregistrationno
is NOT NULL OR
p.preregistrationno <> ''))THEN
'Expired'
ELSE
''
END)PRNStatus,
p.UpdatedBy,
p.UpdatedDate,
p.Status,
NULL
as Draft,
NULL
as TempDraftID,
NULL
as IsMlccase,
NULL
as MlcCaseNo,
NULL
as IsHyperTension,
NULL
as havecommunicabledisease,
NULL
as patientpreference,
NULL
as foodpreference,
NULL
as diabetictype,
NULL
as deathdatetime,
NULL
as EmployeeRelation,
NULL
as EventID,
NULL
as EventName,
NULL
as EventType,
P.FIRSTNAME
as FirstName1,
P.LastName
as LastName1,
NULL
as ReferralPatientUHID,
p.flag
as flag,
p.regularizationcheck
as regularization,
NULL
as Emergencyflag,
'Y' ENTERPRISEFLAG,
ERM.REGIONNAME
from REGISTRATION.MV_ENT_PATIENT_DETAILS p
LEFT OUTER JOIN EHIS.Titlemaster TM ON p.title = tm.titlecode
LEFT OUTER JOIN EHIS.SuffixMaster SM on p.sufix = SM.SUFFIXCODE
LEFT OUTER JOIN EHIS.Maritalstatusmaster MSM ON MSM.MARITALSTATUSID = p.maritalstatus::NUMERIC
LEFT OUTER JOIN EHIS.Bloodgroupmaster BGM ON BGM.BLOODGROUPID = p.bloodgroup::NUMERIC
LEFT OUTER JOIN EHIS.LovDetail LD ON(LD.LOVDETAILID = p.gender::NUMERIC AND LD.LOVID = ln_genderLovID)
LEFT OUTER JOIN EHIS.LovDetail rf ON(rf.LOVDETAILID = p.rhfactor::NUMERIC AND rf.LOVID = ln_rhfactorLovID)
LEFT OUTER JOIN EHIS.PRIVACYMASTER PM ON P.PRIVACYSTATUS::numeric = PM.PRIVACYID
JOIN EHIS.REGIONMAPPINGMASTER RMM
ON ROWNUM::numeric = 1
AND RMM.STATUS = 1
AND RMM.CHARTID::numeric = P.LOCATIONID
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
UHID,(SELECT RegistrationType
from REGISTRATION.registrationmaster
WHERE Registrationid = in_RegistrationID::numeric)RegistrationType,
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
TM.TITLETYPE,(case
when(p.reasonforfree = 'Quick Registration' and
p.regularizationcheck = 0)then
'NOTREGULARIZED'
when(p.reasonforfree = 'Quick Registration' and
p.regularizationcheck = 1)then
'REGULARIZED'
else
'Registration'
end)
as regularizationcheck,(CASE
WHEN UPPER(PM.PRIVACYTYPE)= 'VERY HIGH' THEN
P.ALIASNAME
ELSE
P.FirstName
END)
as FirstName,
MiddleName,(CASE
WHEN UPPER(PM.PRIVACYTYPE)= 'VERY HIGH' THEN
''
ELSE
P.LastName
END)
as LastName,
TM.TITLETYPE || ' ' || FirstName || ' ' || ' ' || MiddleName || ' ' ||
LastName || ' ' || SM.SUFFIXNAME
as PatientName,
Sufix,
SM.SUFFIXNAME SuffixName,
EducationalQualification,
OtherDegree,
to_char(BirthDate, 'DD - MON - YYYY')BirthDate,
to_char(BirthTime, 'DD - MON - YYYY HH24:MI:SS')BirthTime,
FatherName,
SpouseName,
MotherMaidenName,
GaurdianName,
Birthplace,
Approximate,
floor(oracle.months_between(current_timestamp(0)::timestamp, BirthDate)/12)||' - Yrs '|| floor(mod(oracle.months_between(current_timestamp(0)::timestamp, BirthDate),12))||' - Months'
as Age,
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
CustomerStatus,(SELECT L.LOVDETAILID FROM ehis.lovdetail L WHERE upper(L.LOVDETAILVALUE)= upper(CustomerStatus))
as CustomerStatusID ,
p.AliasName,
StartDate,
EndDate,
NoOfIssues,(CASE
WHEN(((p.createddate + ln_PRNExpiryDuration)< current_timestamp(0)::timestamp)AND(p.preregistrationno
is NOT NULL OR
p.preregistrationno <> ''))THEN
'Expired'
ELSE
''
END)PRNStatus,
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
TO_CHAR(deathdatetime, 'DD - MON - YYYY HH24:MI:SS')
as deathdatetime,
EmployeeRelation,
EventID,
EventName,
EventType,
P.FIRSTNAME
as FirstName1,
P.LastName
as LastName1,
ReferralPatientUHID,
p.flag
as flag,
p.regularizationcheck
as regularization,
P.Emergencyflag,
NULL
as ENTERPRISEFLAG,
NULL
as REGIONNAME
from REGISTRATION.PATIENT p
LEFT OUTER JOIN EHIS.Titlemaster TM ON p.title = tm.titlecode
LEFT OUTER JOIN EHIS.SuffixMaster SM on p.sufix = SM.SUFFIXCODE
LEFT OUTER JOIN EHIS.Maritalstatusmaster MSM ON MSM.MARITALSTATUSID = p.maritalstatus::NUMERIC
LEFT OUTER JOIN EHIS.Bloodgroupmaster BGM ON BGM.BLOODGROUPID = p.bloodgroup::NUMERIC
LEFT OUTER JOIN EHIS.LovDetail LD ON(LD.LOVDETAILID = p.gender::NUMERIC AND LD.LOVID = ln_genderLovID)
LEFT OUTER JOIN EHIS.LovDetail rf ON(rf.LOVDETAILID = p.rhfactor::NUMERIC AND rf.LOVID = ln_rhfactorLovID)
LEFT OUTER JOIN EHIS.PRIVACYMASTER PM ON P.PRIVACYSTATUS::numeric = PM.PRIVACYID
WHERE RegistrationID = in_RegistrationID AND((p.Status = 1 OR p.draft = 1));
END IF;
/*
 COMMIT;
*/

/*
OPEN ocursor_Component2
 FOR
 SELECT RegistrationID,ResidenceNumber,MobileNumber,PrimaryEmail,Country,State,District,City,Address1,Address2,Pincode
 FROM AddressMaster
 WHERE UPPER(RegistrationID)=UPPER(in_RegistrationID) AND Status=1
 AND AddressTypeID=(SELECT AddressTypeID FROM AddressTypeMaster
 WHERE AddressTypeName='PermanentAddress');
*/

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
from REGISTRATION.AddressMaster amr
WHERE RegistrationID = in_RegistrationID AND amr.Status = 1 AND
AddressTypeID =(SELECT AddressTypeID
from REGISTRATION.AddressTypeMaster
WHERE AddressTypeName = 'PERMANENTADDRESS');
/*
 COMMIT;
*/

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
from REGISTRATION.AddressMaster am LEFT OUTER JOIN EHIS.Countrymaster CM ON CM.COUNTRYID = am.country LEFT OUTER JOIN EHIS.Statemaster SM ON SM.STATEID = am.state AND SM.COUNTRYID = AM.COUNTRY LEFT OUTER JOIN EHIS.Districtmaster DM ON DM.DISTRICTID = am.district AND DM.STATEID = AM.STATE LEFT OUTER JOIN EHIS.Citymaster CM1 ON CM1.CITYID = am.city AND CM1.DISTRICTID = AM.DISTRICT
WHERE RegistrationID = in_RegistrationID AND am.Status = 1 AND
AddressTypeID =(SELECT AddressTypeID
from REGISTRATION.AddressTypeMaster
WHERE AddressTypeName = 'CURRENTADDRESS');
/*
 COMMIT;
*/

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
from REGISTRATION.PatientWorkplaceDetail PWD INNER JOIN REGISTRATION.AddressMaster AM ON PWD.RegistrationID = AM.RegistrationID
WHERE PWD.RegistrationID = in_RegistrationID::numeric AND PWD.Status = 1 AND
AddressTypeID =(SELECT AddressTypeID
from REGISTRATION.AddressTypeMaster
WHERE AddressTypeName = 'PATIENTWORKPLACEDETAIL');
/*
 COMMIT;
*/

OPEN ocursor_Component6 FOR
SELECT ContactPersonName,
Gender,
TO_CHAR(BirthDate, 'DD-MON-YYYY')
as BirthDate,
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
from REGISTRATION.ContactPersonDetail CPD LEFT OUTER JOIN REGISTRATION.AddressMaster AM ON CPD.RegistrationID = AM.RegistrationID
WHERE CPD.RegistrationID = in_RegistrationID::numeric AND CPD.Status = 1 AND
AddressTypeID =(SELECT AddressTypeID
from REGISTRATION.AddressTypeMaster
WHERE AddressTypeName = 'EMERGENCYADDRESS');
/*
 COMMIT;
*/

OPEN ocursor_Component7 FOR
SELECT p.REFFERALDOCTORID
FROM Patient p
WHERE RegistrationID = in_RegistrationID;
/*
 COMMIT;
*/

OPEN ocursor_Component8 FOR
SELECT p.REFFERALENTITYID
from REGISTRATION.PATIENT p
WHERE RegistrationID = in_RegistrationID;
/*
 COMMIT;
*/

OPEN ocursor_Component9 FOR
SELECT habit
from REGISTRATION.PatientHabit
WHERE RegistrationID = in_RegistrationID;
/*
 COMMIT;
*/

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
PrimaryPayerid
as PrimaryPayerID,
PayerName
as PrimaryPayerName,
to_char(ID.IssueDate, 'DD-MON-YYYY')IssueDate,
to_char(ID.ExpiryDate, 'DD-MON-YYYY')ExpiryDate,
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
from REGISTRATION.InsuranceDetails ID LEFT OUTER JOIN EHIS.RelationshipMaster RM on ID.Subscriberrelationship = RM.RELATIONSHIPCODE LEFT OUTER JOIN REGISTRATION.AGREEMENTS AG ON ID.AGGREMENT::numeric = AG.AGREEMENTID
WHERE ID.RegistrationID = in_RegistrationID::numeric AND ID.STATUS = 1 AND
to_date(ID.ExpiryDate)> current_timestamp(0)::timestamp;
/*
 COMMIT;
*/

OPEN OCURSOR_COMPONENT11 FOR
SELECT LD.ALLERGYTYPEID
as ALLERGENTYPEID,
LD.ALLERGYTYPENAME
as ALLERGENTYPE,
ASM.ALLERGYSEVERITYID
as ALLERGENSEVERITYID,
ASM.ALLERGYSEVERITYNAME
as ALLERGYSEVERITY,
coalesce(AM.ALLERGENID, AGM.GROUPID)
as ALLERGENID,
coalesce(coalesce(AM.ALLERGENNAME, AGM.GROUPNAME), PA.ALLERGEN_NAME)
as ALLERGEN,
PA.ALLERGYDESC
as ALLERGYDESCRIPTIONID,
case when PA.GROUPID is not null then '1' else '0' endISGROUP,
pa.status,
PA.Patientallergy_Id,
ASM.SEVERITYTOOLTIP
as TOOLTIP,
ASM.OVERRIDE,
AM.GENERICNAME
as GENERICNAME,
PA.INACTIVATEREASON,
PA.INACTIVATEDATE,
TO_CHAR(PA.createddate, 'MM/DD/YYYY HH:MI:SS AM')
as createddate,
null
as FLAG1,
CASE
WHEN PA.STATUS = 2 OR PA.STATUS = 6 THEN 1
else 0
END
as "SORTSTATUS"
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
PA.STATUS <> 0
and PA.STATUS = 1
AND PA.REGISTRATIONID = IN_REGISTRATIONID::numeric
order by SORTSTATUS;
/*
 COMMIT;
*/

OPEN ocursor_Component12 FOR
SELECT p.CORPORATEID
FROM Patient p
WHERE RegistrationID = in_RegistrationID;
/*
 COMMIT;
*/

OPEN ocursor_Component13 FOR
SELECT Nationality,
InternationalPatient,
CountryIssued,
PassportNumber,
TO_CHAR(PassportIssuedate, 'DD-MON-YYYY')
as PassportIssuedate,
TO_CHAR(PassportExpirydate, 'DD-MON-YYYY')
as PassportExpirydate,
VisaType,
VisaIssuingAuthority,
TO_CHAR(VisaIssueDate, 'DD-MON-YYYY')
as VisaIssueDate,
TO_CHAR(VisaExpiryDate, 'DD-MON-YYYY')
as VisaExpiryDate,
StartDate,
EndDate
FROM Registration.PatientVisaDetail
WHERE RegistrationID = in_RegistrationID AND Status = 1;
/*
 COMMIT;
*/

OPEN ocursor_Component14 FOR
SELECT PatientFileType, PatientFileName, PatientFilePath
from REGISTRATION.PatientExternalMedicalRecords
WHERE RegistrationID = in_RegistrationID AND Status = 1;
/*
 COMMIT;
*/

OPEN ocursor_Component15 FOR
SELECT EmailID, UserID, HintQuestion, HintAnswer
from REGISTRATION.LoginDetails
WHERE RegistrationID = in_RegistrationID;
/*
Open ocursor_Component16 FOR
 select LINKEDUHID
 from REGISTRATION.LINKEDUHID
 WHERE ParentUHID = in_UHID and Status = 1;
 OPEN ocursor_Component17 FOR
 select MERGEDUHID
 from REGISTRATION.MERGEDUHID
 WHERE ParentUHID = in_UHID and Status = 1;
*/

/*

 COMMIT;
 EXCEPTION
 WHEN OTHERS THEN
 DBMS_OUTPUT.PUT_LINE(TO_CHAR(SQLCODE) || SQLERRM);
*/

end;
$BODY$
;



