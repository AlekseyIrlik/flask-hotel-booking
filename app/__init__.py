from flask import Flask

def create_app():
	"Функция по сборке приложения"
	app = Flask(__name__)

	return app