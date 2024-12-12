CREATE TABLE Material (
	Name TEXT PRIMARY KEY,
	Volume INTEGER NOT NULL,
	Mass REAL NOT NULL
) WITHOUT ROWID;

CREATE TABLE MaterialProperty (
	Name TEXT PRIMARY KEY
) WITHOUT ROWID;

CREATE TABLE MaterialPropertyLink (
	MaterialName TEXT NOT NULL,
	MaterialPropertyName TEXT NOT NULL,
	Value REAL,
	PRIMARY KEY (MaterialName, MaterialPropertyName),
	FOREIGN KEY (MaterialName) REFERENCES Material(Name),
	FOREIGN KEY (MaterialPropertyName) REFERENCES MaterialProperty(Name)
) WITHOUT ROWID;

CREATE TABLE BOM (
	Product TEXT NOT NULL,
	Component TEXT NOT NULL,
	Quantity INTEGER NOT NULL,
	PRIMARY KEY (Product, Component),
	FOREIGN KEY (Product) REFERENCES Material(Name),
	FOREIGN KEY (Component) REFERENCES Material(Name)
) WITHOUT ROWID;

CREATE TABLE Distribution (
	ID INTEGER PRIMARY KEY,
	Type TEXT NOT NULL,
	Min REAL,
	Max REAL,
	Avg REAL,
	Std REAL
);

CREATE TABLE Disturbance (
	ID INTEGER PRIMARY KEY,
	Probability REAL NOT NULL,
	Duration INTEGER NOT NULL,
	Loss REAL NOT NULL,
	FOREIGN KEY (Duration) REFERENCES Distribution(ID)
);

CREATE TABLE CostCenter (
	Name TEXT PRIMARY KEY
) WITHOUT ROWID;

CREATE TABLE OperationProperty (
	Name TEXT PRIMARY KEY
) WITHOUT ROWID;

CREATE TABLE OperationPropertyClass (
	ID INTEGER PRIMARY KEY
);

CREATE TABLE OperationPropertyLink (
	ClassID INTEGER NOT NULL,
	OperationProperty TEXT NOT NULL,
	Value REAL NOT NULL,
	PRIMARY KEY (ClassID, OperationProperty),
	FOREIGN KEY (ClassID) REFERENCES OperationPropertyClass(ID),
	FOREIGN KEY (OperationProperty) REFERENCES OperationProperty(Name)
) WITHOUT ROWID;


CREATE TABLE NetworkNode (
	Name TEXT PRIMARY KEY,
	Latitude REAL NOT NULL,
	Longitude REAL NOT NULL,
	CostCenter TEXT,
	DisturbanceID INTEGER,
	FOREIGN KEY (CostCenter) REFERENCES Name(ID),
	FOREIGN KEY (DisturbanceID) REFERENCES Disturbance(ID)
) WITHOUT ROWID;

CREATE TABLE Customer (
	NetworkNode TEXT PRIMARY KEY,
	FOREIGN KEY (NetworkNode) REFERENCES NetworkNode(Name)
) WITHOUT ROWID;

CREATE TABLE DistributionCenter (
	NetworkNode TEXT PRIMARY KEY,
	CapacityLimit INTEGER,
	OperationPropertyID INTEGER,
	FOREIGN KEY (NetworkNode) REFERENCES NetworkNode(Name),
	FOREIGN KEY (OperationPropertyID) REFERENCES OperationPropertyLink(ID)
) WITHOUT ROWID;

CREATE TABLE CollectionCenter (
	NetworkNode TEXT PRIMARY KEY,
	CapacityLimit INTEGER,
	OperationPropertyID INTEGER,
	FOREIGN KEY (NetworkNode) REFERENCES NetworkNode(Name),
	FOREIGN KEY (OperationPropertyID) REFERENCES OperationPropertyLink(ID)
) WITHOUT ROWID;

CREATE TABLE ProductionSite (
	NetworkNode TEXT PRIMARY KEY,
	CapacityLimit INTEGER,
	FOREIGN KEY (NetworkNode) REFERENCES NetworkNode(Name)
) WITHOUT ROWID;

CREATE TABLE RecoveryPlant (
	NetworkNode TEXT PRIMARY KEY,
	CapacityLimit INTEGER,
	FOREIGN KEY (NetworkNode) REFERENCES NetworkNode(Name)
) WITHOUT ROWID;

CREATE TABLE Validity (
	NetworkNode TEXT PRIMARY KEY,
	Start DATE,
	End DATE,
	FOREIGN KEY (NetworkNode) REFERENCES NetworkNode(Name)
) WITHOUT ROWID;

CREATE TABLE Inventory (
	Material TEXT NOT NULL,
	NetworkNode TEXT NOT NULL,
	Quantity INTEGER NOT NULL,
	Price REAL NOT NULL,
	PRIMARY KEY (Material, NetworkNode),
	FOREIGN KEY (Material) REFERENCES Material(Name),
	FOREIGN KEY (NetworkNode) REFERENCES NetworkNode(Name)
) WITHOUT ROWID;

CREATE TABLE ProducedMaterial (
	ProductionSite TEXT NOT NULL,
	MaterialName TEXT NOT NULL,
	Cost REAL NOT NULL,
	Time INTEGER NOT NULL,
	CapacityUsage INTEGER NOT NULL,
	Price REAL NOT NULL,
	OperationPropertyID INTEGER,
	FOREIGN KEY (ProductionSite) REFERENCES NetworkNode(Name),
	FOREIGN KEY (MaterialName) REFERENCES Material(Name),
	FOREIGN KEY (OperationPropertyID) REFERENCES OperationPropertyLink(ID)
);

CREATE TABLE DisassembledMaterial (
	Product TEXT NOT NULL,
	RecoveryPlant TEXT NOT NULL,
	Cost REAL NOT NULL,
	Time INTEGER NOT NULL,
	CapacityUsage INTEGER NOT NULL,
	OperationPropertyID INTEGER,
	PRIMARY KEY (Product, RecoveryPlant),
	FOREIGN KEY (Product) REFERENCES Material(Name),
	FOREIGN KEY (RecoveryPlant) REFERENCES NetworkNode(Name),
	FOREIGN KEY (OperationPropertyID) REFERENCES OperationPropertyLink(ID)
) WITHOUT ROWID;

CREATE TABLE InverseBOM (
	Product TEXT NOT NULL,
	RecoveryPlant TEXT NOT NULL,
	Component TEXT NOT NULL,
	Quantity INTEGER NOT NULL,
	Price REAL NOT NULL,
	FOREIGN KEY (Product) REFERENCES DisassembledMaterial(Product),
	FOREIGN KEY (RecoveryPlant) REFERENCES DisassembledMaterial(RecoveryPlant),
	FOREIGN KEY (Component) REFERENCES Material(Name),
	FOREIGN KEY (Quantity) REFERENCES Distribution(ID)
);

CREATE TABLE Demand (
	Customer TEXT NOT NULL,
	Material TEXT NOT NULL,
	Frequency INTEGER NOT NULL,
	Quantity INTEGER NOT NULL,
	IsBacklog INTEGER NOT NULL,
	AdditionalTrend REAL NOT NULL,
	MultiplicativeTrend REAL NOT NULL,
	Duedate INTEGER NOT NULL,
	WasteProduction REAL NOT NULL,
	FOREIGN KEY (Customer) REFERENCES Customer(NetworkNode),
	FOREIGN KEY (Material) REFERENCES Material(Name),
	FOREIGN KEY (Quantity) REFERENCES Distribution(ID)
);

CREATE TABLE TransportMode (
	Name TEXT PRIMARY KEY,
	FixedCost REAL NOT NULL,
	DistanceCost REAL NOT NULL,
	Time INTEGER NOT NULL,
	DisturbanceID INTEGER,
	OperationPropertyID INTEGER,
	FOREIGN KEY (DisturbanceID) REFERENCES Disturbance(ID),
	FOREIGN KEY (OperationPropertyID) REFERENCES OperationPropertyLink(ID)
) WITHOUT ROWID;

CREATE TABLE Route (
	Source TEXT NOT NULL,
	Destination TEXT NOT NULL,
	TransportMode  TEXT NOT NULL,
	CostCenter TEXT,
	FOREIGN KEY (Source) REFERENCES NetworkNode(Name),
	FOREIGN KEY (Destination) REFERENCES NetworkNode(Name),
	FOREIGN KEY (TransportMode) REFERENCES TransportMode(Name),
	FOREIGN KEY (CostCenter) REFERENCES CostCenter(Name)
);

CREATE TABLE SimulationResult (
	ID INTEGER PRIMARY KEY,
	CostCenter TEXT NOT NULL,
	KPI TEXT NOT NULL,
	Value REAL NOT NULL,
	FOREIGN KEY (CostCenter) REFERENCES CostCenter(Name)
);