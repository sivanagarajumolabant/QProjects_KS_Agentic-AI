CREATE OR REPLACE PROCEDURE ahc.GETCOPD (iv_AHCNo IN ahc.COPDAPIRESPONSEDATA.ADMISSIONNUMBER%TYPE, oCursor_copd INOUT refcursor)
/*
 *****************************************************************************
 Procedure: GetCOPD
 Parameters: @Ahcno,@UHID Id INPUT
 Purpose: This procedure is to gets APIResponse details from COPDAPIResponse.
 Created By: Aman Saxena on 03072021
 *****************************************************************************
 */
LANGUAGE plpgsql
SECURITY DEFINER
AS $BODY$
BEGIN
    SET search_path TO AHC;
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
            risk_text AS RiskText,
            Testsfollowup
        FROM
            ahc.COPDAPIRESPONSEDATA
        WHERE
            ADMISSIONNUMBER = iv_AHCNo;
END;
$BODY$;




