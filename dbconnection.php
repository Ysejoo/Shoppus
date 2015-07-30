<?
session_start();
$mysql_hostname = "localhost";
$mysql_user = "root";
$mysql_password = "apmsetup";
$mysql_database = "shoppus";

$bd = mysql_connect($mysql_hostname, $mysql_user, $mysql_password) or die("db connect error");
mysql_select_db($mysql_database, $bd) or die("db connect error");
mysql_query("set session character_set_connection=utf8;");

mysql_query("set session character_set_results=utf8;");

mysql_query("set session character_set_client=utf8;");
?>

