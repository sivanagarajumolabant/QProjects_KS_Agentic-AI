
  CREATE OR REPLACE  PROCEDURE "AHC"."GETCOPD" (iv_AHCNo IN COPDAPIRESPONSEDATA.ADMISSIONNUMBER%TYPE,
                                                        oCursor_copd OUT SYS_REFCURSOR)
/******************************************************************************
    Procedure:  GetCOPD
    Parameters: @Ahcno,@UHID Id INPUT
    Purpose:    This procedure is to gets  APIResponse details from COPDAPIResponse.
    Created By: Aman Saxena on 03/07/2021
  ******************************************************************************/
 AS
BEGIN
  OPEN oCursor_copd FOR
    SELECT
      UHID,
      ADMISSIONNUMBER,
      PatientName,
      MobileNo,
      Location,
      RepiratoryCondition,
      AgeStatus,
      GenderStatus,
      Tobaccoproducts,
      HertDisease,
      Progressivebreathlessness,
      Sputumproduction,
      DrugsListedBelow,
      RespiratoryRate,
      BaselineRecently,
      OxygenSaturation,
      ChestAuscultation,
      LabInvestigation,
      DiagnosticsorImaging,
      Referral,
      TreatmentGoals,
      EDUCATEOn,
      CREATEDDATE,
      UPDATEDDATE,
      GENDER,
      RISK,
      AGE,
      Nextsteps,
      risk_text as RiskText,
      Testsfollowup
      FROM  AHC.COPDAPIRESPONSEDATA
      WHERE ADMISSIONNUMBER = iv_AHCNo;

END GetCOPD;