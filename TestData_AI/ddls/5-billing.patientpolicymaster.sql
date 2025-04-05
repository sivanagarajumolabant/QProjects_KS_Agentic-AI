CREATE TABLE billing.patientpolicymaster (
	patientpolicymasterid numeric NOT NULL,
	locationid varchar(50) NULL,
	registrationno varchar(100) NOT NULL,
	billingtypeid numeric NULL,
	createdby varchar(100) NULL,
	createddte timestamp NULL,
	updatedby varchar(100) NULL,
	updateddate timestamp NULL,
	CONSTRAINT pk_policymaster PRIMARY KEY (patientpolicymasterid)
);