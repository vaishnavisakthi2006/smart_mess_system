import pandas as pd
def load_users():
    return pd.read_csv("datasets/users.csv")
def load_admin_registers():
    return pd.read_csv("datasets/admin_registers.csv")
def load_menu():
    return pd.read_csv("datasets/mess_menu.csv")
def load_ratings():
    return pd.read_csv("datasets/student_ratings.csv")