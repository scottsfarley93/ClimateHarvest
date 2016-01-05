<?php
	//phpinfo();
     $connection_string = "dbname=climateHarvest host=localhost user=postgres port=5432";
     $conn = pg_connect($connection_string);
	 if(!$conn){
		 die("Failed to connect to database: " . pg_errormessage($conn));
	 }
	 echo "Connected to database.";
	
?>