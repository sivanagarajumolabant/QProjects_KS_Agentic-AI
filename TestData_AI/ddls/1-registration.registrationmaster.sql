CREATE TABLE registration.registrationmaster (
	registrationid numeric(19) NOT NULL,
	registrationtype numeric(10) NOT NULL,
	registrationsource varchar(100) NULL,
	registrationdescription varchar(100) NULL,
	updateddate timestamp NOT NULL,
	updatedby varchar(100) NOT NULL,
	CONSTRAINT pk_registrationmaster PRIMARY KEY (registrationid)
);