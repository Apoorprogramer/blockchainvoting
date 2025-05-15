from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import hashlib
import time

app = Flask(__name__)

# Create a new blockchain
class Block:
    def __init__(self, index, previous_hash, timestamp, voter_id, candidate_id, vote):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.voter_id = voter_id
        self.candidate_id = candidate_id
        self.vote = vote
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        data = str(self.index) + self.previous_hash + str(self.timestamp) + str(self.voter_id) + str(self.candidate_id) + str(self.vote)
        return hashlib.sha256(data.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_votes = []

    def create_genesis_block(self):
        return Block(0, "0", int(time.time()), None, None, None)

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.hash = new_block.calculate_hash()
        self.chain.append(new_block)

    def get_latest_block(self):
        return self.chain[-1]

# Create a new blockchain
voting_system = Blockchain()

# Connect to the SQLite database
conn = sqlite3.connect('voting_system.db')
c = conn.cursor()

# Create table
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username text, password text)''')

c.execute('''CREATE TABLE IF NOT EXISTS candidates
             (name text)''')

c.execute('''CREATE TABLE IF NOT EXISTS votes
             (voter_id text, candidate_id text)''')

conn.commit()
conn.close()

# Default admin credentials
admin_username = 'admin'
admin_password = 'password'

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/result')
def result():
    conn = sqlite3.connect('voting_system.db')
    c = conn.cursor()
    c.execute("SELECT * FROM votes")
    votes = c.fetchall()
    conn.close()

    # Count the votes for each candidate
    candidates = {}
    for vote in votes:
        if len(vote) > 1:
            candidate_id = vote[1]
            if candidate_id in candidates:
                candidates[candidate_id] += 1
            else:
                candidates[candidate_id] = 1
        else:
            print("Error: vote tuple has only one element")

    # Get the candidate names
    conn = sqlite3.connect('voting_system.db')
    c = conn.cursor()
    c.execute("SELECT * FROM candidates")
    candidate_names = {}
    for row in c.fetchall():
        if len(row) > 0:
            candidate_names[row[0]] = row[0]
        else:
            print("Error: candidate row is empty")
    conn.close()

    # Create a dictionary to store the results
    results = {}
    for candidate_id, count in candidates.items():
        if candidate_id in candidate_names:
            results[candidate_names[candidate_id]] = count
        else:
            print("Error: candidate_id not found in candidate_names")

    return render_template('result.html', results=results)
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('voting_system.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        return redirect(url_for('voting_page'))
    else:
        return 'Invalid username or password'

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('voting_system.db')
    c = conn.cursor()
    c.execute("INSERT INTO users VALUES (?,?)", (username, password))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == admin_username and password == admin_password:
            return render_template('admin.html')
        else:
            return '<div style="display: flex; align-items: center; justify-content: center; height: 100vh;  margin: 20px;"><b style="background-color: red; color: white; font-size: 20px; padding: 10px; margin: 10px; border: 1px solid black; border-radius: 5px;">Invalid admin credentials</b></div>'
    return render_template('admin_login.html')

@app.route('/add_candidate', methods=['POST'])
def add_candidate():
    name = request.form['name']
    conn = sqlite3.connect('voting_system.db')
    c = conn.cursor()
    c.execute("INSERT INTO candidates VALUES (?)", (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/voting_page')
def voting_page():
    conn = sqlite3.connect('voting_system.db')
    c = conn.cursor()
    c.execute("SELECT * FROM candidates")
    candidates = c.fetchall()
    conn.close()
    return render_template('voting_page.html', candidates=candidates)

@app.route('/cast_vote', methods=['POST'])
def cast_vote():
    candidate_id = request.form['candidate_id']
    voter_id = request.form['voter_id']
    
    # Check if the voter has already voted
    conn = sqlite3.connect('voting_system.db')
    c = conn.cursor()
    c.execute("SELECT * FROM votes WHERE voter_id=?", (voter_id,))
    existing_vote = c.fetchone()
    conn.close()
    
    if existing_vote:
        return 'You have already voted.'
    
    # Cast the vote
    new_block = Block(len(voting_system.chain), voting_system.get_latest_block().hash, int(time.time()), voter_id, candidate_id, True)
    voting_system.add_block(new_block)
    conn = sqlite3.connect('voting_system.db')
    c = conn.cursor()
    c.execute("INSERT INTO votes VALUES (?,?)", (voter_id, candidate_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)