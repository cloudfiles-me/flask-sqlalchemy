import boto3
import ast
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db_driver='mysql://'
db_name='rdsfailover'

secret_name = "rds_app_user"
endpoint_url = "https://secretsmanager.us-east-1.amazonaws.com"
region_name = "us-east-1"

session = boto3.session.Session()
client = session.client(
    service_name='secretsmanager',
    region_name=region_name
)

try:
    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
        print("The requested secret " + secret_name + " was not found")
    elif e.response['Error']['Code'] == 'InvalidRequestException':
        print("The request was invalid due to:", e)
    elif e.response['Error']['Code'] == 'InvalidParameterException':
        print("The request had invalid params:", e)
else:
    # Decrypted secret using the associated KMS CMK
    # Depending on whether the secret was a string or binary, one of these fields will be populated
    secret = get_secret_value_response['SecretString']
    secret = ast.literal_eval(secret)
    # db_uri example
    # mysql://username:password@db_server_endpoint/dbname
    db_uri = db_driver + secret['username'] + ":" + secret['password'] + "@" + secret['host'] + "/" + db_name
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)

    class Rdsfailover(db.Model):
        __tablename__ = 'failover_test'
        id = db.Column(db.Integer, primary_key=True)
        test_name = db.Column(db.String(50))
        failover_date = db.Column(db.Date)

    results = Rdsfailover.query.all()
    for item in results:
        print(item.failover_date)

# Example of String returned by Secrets Manager
# {"username":"username","password":"password","engine":"mysql","host":"rds_endpoint","port":3306,"dbname":"dbname","dbInstanceIdentifier":"db_instance_Id"}
