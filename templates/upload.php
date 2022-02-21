<?php
$allowed_file_types = ['image/jpeg', 'image/png'];
$allowed_size_mb = 2; 

// validate upload error
switch($_FILES['file']['error']) {
	// no error
	case UPLOAD_ERR_OK:
		break;

	// no file
	case UPLOAD_ERR_NO_FILE:
		exit('Error : No file send as attachment');

	// php.ini file size exceeded 
	case UPLOAD_ERR_INI_SIZE:
		exit('Error : File size exceeded as set in php.ini');

	// other upload error
	default:
        exit('Error : File upload failed');
}

// validate file type from file data
$finfo = finfo_open();
$file_type = finfo_buffer($finfo, file_get_contents($_FILES['file']['tmp_name']), FILEINFO_MIME_TYPE);
if(!in_array($file_type, $allowed_file_types))
	exit('Error : Incorrect file type');

// validate file size
$file_size = $_FILES['file']['size'];
if($file_size > $allowed_size_mb*1024*1024)
	exit('Error : Exceeded size');

// safe unique name from file data
$file_unique_name = sha1_file($_FILES['file']['tmp_name']);
$file_extension = strtolower(pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION));
$file_name = $file_unique_name . '.' . $file_extension;

$destination = '/static/upload/' . $file_name;

// save file to destination
if(move_uploaded_file($_FILES['file']['tmp_name'], $destination) === TRUE)
	echo 'File uploaded successfully';
else
	echo 'Error: Uploaded file failed to be saved';
?>