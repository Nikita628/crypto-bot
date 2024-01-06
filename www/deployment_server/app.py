from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def do_post():
    if request.method == 'POST':
        if request.args.get('ref') == 'refs/heads/migrations_and_python_server':
            with open('./output.txt', 'a') as f:
                f.write('Hi')
            return 'r'
        else:
            with open('./output.txt', 'a') as f:
                f.write('TTTTT')
            return 'post'
    else:
        return 'not post request'

if __name__ == '__main__':
    app.run(debug=True)