from src.Appointment import Appointment


def main():
    #app = Appointment("moskau", "nationaleVisa")
    app = Appointment("kiew", "nationaleVisa")
    app.try_monthly_appointments()

if __name__ == "__main__":
    main()
