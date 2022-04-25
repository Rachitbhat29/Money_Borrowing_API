Money Borrowing API APP
----------
----------


Quickstart
----------

Application is up on 
[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

`database2.db` (SQLite) includes 2 tables:

* User table for storing user records for login.
* Transaction_list table for storing all transactions all users.

API Details
----------------------

This example server application features, multiple APIs endpoints, supporting few CRUD opeartions. like as below

* Login : It accepts username and password and returns true if exists.
* add_transaction : it accepts { user_id, transaction_id (random hash), transaction_type (borrow/lend), transaction_amount (negative, positive), transaction_date, transaction_status (paid/unpaid), transaction_with (user_id) }.
* mark_paid : it accepts transaction id  and changes transaction status.
* get_transactions : fetches all the transactions for the user (he can be either borrower or lender).
* credit_score : it sends the user’s credit score based on his/her transaction history.

### Login API endpoint for Authentication with Username and Password

Here is how you use login API to authenticate with user login and password credentials using cURL:

```
$ curl -X POST "http://127.0.0.1:5000/login" -H  "accept: */*" -H  "Content-Type: application/json" -d "{\"username\":\"rachit\",\"password\":\"rachit123\"}"
```

Well, the above request uses json object to pass username and
password. And password is applied with sha256 alogrithm for encrypting and checked with the stored values in Db. 


### Add Transaction API endpoint for adding transaction.

```
$ curl -i -H "Content-Type: application/json;charset=utf-8" POST --data "{\"transaction_from\":1,\"transaction_type\":\"B\",\"transaction_amount\":200,\"transaction_status\":\"Unpaid\",\"transaction_with\":2,\"reason\":\"loan\"}" http://localhost:5000/add_transaction
```

![img_3](https://user-images.githubusercontent.com/36357104/165146688-efffa3e8-d75c-4c15-a0ce-07c00789db22.png)


This included a transaction in the Db. User need to send payload with below values
```
{ user_id, transaction_id (random hash), transaction_type (borrow/lend), transaction_amount (negative, positive), transaction_date, transaction_status (paid/unpaid), transaction_with (user_id) }
```

### Get all Transaction API endpoint for getting all transactions for a specific user.

```
$ curl 'http://localhost:5000/get_transactions/1'
```

Here we need to specify the user_id in the Url for getting the specific users trnsactions.


### Marks Paid API endpoint for marking paid to specific trnsaction.

This is the PATCH http request for updating the trnsaction_status as `Paid` for provided transaction_id.

```
$ curl -i -H "Content-Type: application/json;charset=utf-8" -X PATCH --data "{\"transaction_status\":\"Paid\"}" http://localhost:5000/mark_paid/d1a2bcbc-5111-4442-8641-d9ea19b49e22
```

Response:

![img_2](https://user-images.githubusercontent.com/36357104/165146895-83c44c17-d477-4ea7-988e-08db221d0acc.png)


### Credit score API endpoint for generating the credit score based on the all trnsactions made by a user.

Credit score is being calculated for a user for on basis of both borrowing and lending transactions and
send in the response with below formula:

`Formula = % amount borrowed [ 100(>90%), 200 (80%-90%), 300.. 1000 (<10%) ] + % amount lent [1100(<10%), 1200, 1300.. 2000 (>90%)]`

Request follows:
```
$ http://localhost:5000/credit_score/1
```

This is the GET http request for providing the credit score for provided user.

