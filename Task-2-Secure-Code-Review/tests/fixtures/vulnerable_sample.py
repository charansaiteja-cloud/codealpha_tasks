import pickle


def unsafe_function(data):
    return pickle.loads(data)


jwt_secret = "super-secret-production-key-12345"
