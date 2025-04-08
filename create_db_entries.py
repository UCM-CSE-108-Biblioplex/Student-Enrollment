import requests, random, argparse, json

first_names = [
    'Aaron', 'Abel', 'Abigail', 'Ada', 'Adam', 'Addison', 'Adrian', 'Aiden', 'Aimee', 'Ainsley', 'Alan', 'Albert', 'Alex', 'Alexander', 'Alfred', 'Alice', 'Alicia', 'Allison', 'Alonzo', 'Alyssa', 'Amanda', 'Amber', 'Amy', 'Anders', 'Andrea', 'Andrew', 'Andy', 'Angel', 'Angela', 'Anna', 'Anne', 'Anthony', 'April', 'Ariel', 'Arnold', 'Arthur', 'Ash', 'Ashley', 'Audrey', 'Austin', 'Ava', 'Avery', 'Bailey', 'Barbara', 'Barry', 'Becky', 'Bella', 'Benjamin', 'Bernard', 'Bernice', 'Beth', 'Betty', 'Beverly', 'Bill', 'Blair', 'Blake', 'Bobby', 'Bonnie', 'Brad', 'Bradford', 'Bradley', 'Brandon', 'Brenda', 'Brett', 'Brian', 'Brianna', 'Brittany', 'Brooke', 'Bruce', 'Bryan', 'Caitlin', 'Caleb', 'Cameron', 'Camilla', 'Candice', 'Cara', 'Carl', 'Carla', 'Carlos', 'Carol', 'Caroline', 'Carson', 'Casey', 'Catherine', 'Cecilia', 'Chad', 'Charles', 'Charlie', 'Charlotte', 'Chelsea', 'Cheryl', 'Chris', 'Christian', 'Christina', 'Christine', 'Christopher', 'Claire', 'Clara', 'Clarence', 'Claudia', 'Cody', 'Colin', 'Colleen', 'Connie', 'Connor', 'Corey', 'Cornelius', 'Crystal', 'Cynthia', 'Daisy', 'Dale', 'Dallas', 'Dana', 'Daniel', 'Danielle', 'Dante', 'Daphne', 'Darren', 'David', 'Dean', 'Deanna', 'Deborah', 'Denise', 'Dennis', 'Derek', 'Devin', 'Devon', 'Diana', 'Diane', 'Dominic', 'Don', 'Donald', 'Donna', 'Dora', 'Dorian', 'Doris', 'Douglas', 'Drew', 'Dylan', 'Earl', 'Eddie', 'Edith', 'Edmund', 'Edward', 'Elaine', 'Eleanor', 'Elijah', 'Elizabeth', 'Ella', 'Ellen', 'Elliot', 'Ellis', 'Emerson', 'Emery', 'Emily', 'Emma', 'Eric', 'Erica', 'Erin', 'Esther', 'Ethan', 'Eva', 'Evan', 'Evelyn', 'Faith', 'Felicia', 'Felix', 'Finley', 'Fiona', 'Fletcher', 'Frances', 'Francis', 'Frank', 'Frankie', 'Fred', 'Gabriel', 'Gabrielle', 'Gail', 'Gale', 'Gary', 'George', 'Gerald', 'Grace', 'Greg', 'Grey', 'Gunner', 'Hailey', 'Hannah', 'Harley', 'Harper', 'Harrison', 'Harry', 'Hayden', 'Heather', 'Helen', 'Henry', 'Holly', 'Howard', 'Ian', 'Ira', 'Irene', 'Isaac', 'Isabel', 'Isabella', 'Jack', 'Jackie', 'Jackson', 'Jacob', 'Jacqueline', 'Jake', 'James', 'Jamie', 'Jane', 'Janet', 'Janice', 'Jarvis', 'Jasmine', 'Jason', 'Jay', 'Jean', 'Jeff', 'Jeffrey', 'Jennifer', 'Jeremy', 'Jerry', 'Jesse', 'Jessica', 'Jill', 'Jillian', 'Jim', 'Joan', 'Joanne', 'Jocelyn', 'Joe', 'John', 'Johnny', 'Jordan', 'Joseph', 'Josh', 'Joy', 'Joyce', 'Judy', 'Julia', 'Julie', 'Justin', 'Kai', 'Kaitlyn', 'Karen', 'Kate', 'Kathleen', 'Kathryn', 'Katie', 'Kayla', 'Keith', 'Kelly', 'Kelsey', 'Ken', 'Kendall', 'Kendrick', 'Kennedy', 'Kevin', 'Kim', 'Kimberly', 'Kristen', 'Kyle', 'Lance', 'Landry', 'Lane', 'Larry', 'Laura', 'Lauren', 'Lawrence', 'Lawson', 'Leah', 'Lee', 'Leo', 'Leonard', 'Leslie', 'Liam', 'Lillian', 'Linda', 'Lindsay', 'Lisa', 'Logan', 'Lois', 'Lori', 'Louis', 'Louise', 'Lucas', 'Luke', 'Lydia', 'Lynne', 'Mabel', 'Mackenzie', 'Madeline', 'Madison', 'Malcolm', 'Margaret', 'Maria', 'Marie', 'Marilyn', 'Marissa', 'Mark', 'Martha', 'Martin', 'Mary', 'Mason', 'Matthew', 'Maximilian', 'Megan', 'Melanie', 'Melissa', 'Meredith', 'Mia', 'Micah', 'Michael', 'Michelle', 'Mike', 'Mildred', 'Miles', 'Mitchell', 'Monica', 'Morgan', 'Nancy', 'Naomi', 'Natalie', 'Natasha', 'Neil', 'Nelson', 'Nick', 'Nicole', 'Nina', 'Noah', 'Nora', 'Norma', 'Oliver', 'Olivia', 'Orson', 'Oscar', 'Owen', 'Paige', 'Pamela', 'Parker', 'Pat', 'Patricia', 'Patrick', 'Paul', 'Paula', 'Peggy', 'Penelope', 'Peter', 'Peyton', 'Phil', 'Philip', 'Phoebe', 'Phoenix', 'Presley', 'Preston', 'Priscilla', 'Quentin', 'Quinn', 'Rachel', 'Ralph', 'Randy', 'Ray', 'Rebecca', 'Reese', 'Reginald', 'Renee', 'Rhonda', 'Richard', 'Rick', 'Riley', 'Rita', 'River', 'Robert', 'Robin', 'Roger', 'Ron', 'Rory', 'Rose', 'Ross', 'Roy', 'Ruth', 'Ryan', 'Sage', 'Sam', 'Samantha', 'Sandra', 'Sara', 'Sarah', 'Scott', 'Sean', 'Sebastian', 'Seth', 'Shane', 'Shannon', 'Sharon', 'Shawn', 'Sheila', 'Sherry', 'Shirley', 'Sidney', 'Silas', 'Simon', 'Sky', 'Skyler', 'Sofia', 'Sonia', 'Spencer', 'Stan', 'Stephanie', 'Stephen', 'Steve', 'Stuart', 'Susan', 'Sydney', 'Sylvia', 'Tamara', 'Tanya', 'Taylor', 'Teagan', 'Ted', 'Teresa', 'Terry', 'Thaddeus', 'Thomas', 'Tim', 'Tina', 'Todd', 'Tom', 'Tony', 'Tracy', 'Travis', 'Trevor', 'Trisha', 'Tyler', 'Ulrich', 'Val', 'Valerie', 'Vanessa', 'Vaughn', 'Vincent', 'Walter', 'Wayne', 'Whitney', 'William', 'Winston', 'Xavier', 'York', 'Zach', 'Zachary', 'Zane'
]

namelib = []
first_syl = [
    "","","","","A","Be","De","El","Fa","Jo","Ki","La","Ma","Na","O","Pa","Re","Si","Ta","Va"
]
second_syl = [
    "Bar","Ched","Dell","Far","Gran","Hal","Jen","Kel","Lim","Mor","Net","Penn","Quil","Rond","Sark","Shen","Tur","Vash","Yor","Zen"
]
third_syl = [
    "","a","ac","ai","al","am","an","ar","ea","el","er","ess","ett","ic","id","il","in","is","or","us"
]

def create_last_name():
    return((random.choice(first_syl) + random.choice(second_syl) + random.choice(third_syl)).casefold().capitalize())

def create_password(length: str = 16):
    return "".join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_") for i in range(length))

parser = argparse.ArgumentParser()
parser.add_argument(
    "-n", "--number",
    help="Number of entries to create",
    nargs="?",
    default=500,
    const=True
)
args = parser.parse_args()

def create_db_entry(first_name, middle_name, last_name):
    payload = {
        "is_admin": False,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": create_last_name(),
        "email": f"hello+{create_password(8)}@example.com",
        "password": create_password()
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post("http://localhost:5000/api/v1/users", data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        print("f")
    except Exception as e:
        print(e)

if(__name__ == "__main__"):
    number = int(args.number)
    for i in range(number):
        create_db_entry(
            random.choice(first_names),
            random.choice(first_names) if random.choice([True, False]) else "",
            create_last_name()
        )