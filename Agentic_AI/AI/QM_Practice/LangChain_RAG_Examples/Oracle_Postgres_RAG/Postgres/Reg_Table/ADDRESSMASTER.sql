
CREATE TABLE IF NOT EXISTS REGISTRATION.ADDRESSMASTER

(	REGISTRATIONID numeric(19,0),
ADDRESSTYPEID numeric(10,0),
STREET varchar(200),
LOCALITY varchar(200),
COUNTRY numeric(19,0),
STATE numeric(19,0),
DISTRICT numeric(19,0),
CITY numeric(19,0),
ADDRESS1 varchar(500),
ADDRESS2 varchar(500),
RESIDENCENUMBER varchar(100),
OFFICENUMBER varchar(100),
EXTENSION varchar(100),
MOBILENUMBER varchar(100),
EMERGENCYNUMBER varchar(100),
RESIDENCEFAXNUMBER varchar(100),
OFFICEFAXNUMBER varchar(100),
PRIMARYEMAIL varchar(200),
ALTERNATEEMAIL varchar(200),
PINCODE varchar(40),
CONTACTNUMBER1 varchar(100),
CONTACTNUMBER2 varchar(100),
STARTDATE timestamp without time zone ,
ENDDATE timestamp without time zone ,
STATUS numeric(10,0),
UPDATEDBY varchar(100),
UPDATEDDATE timestamp without time zone ,
FLEXIFIELD1 varchar(100),
FLEXIFIELD2 varchar(100));



