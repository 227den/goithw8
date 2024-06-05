import pickle
from collections import UserDict
from datetime import datetime, timedelta, date

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must be 10 digits and contain only digits")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        if isinstance(phone, Phone):
            self.phones.append(phone)
        else:
            self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                break

    def edit_phone(self, old_phone, new_phone):
        for p in self.phones:
            if p.value == old_phone:
                p.value = new_phone
                break

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        birthday = f", Birthday: {self.birthday.value}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{birthday}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        del self.data[name]

    def get_upcoming_birthdays(self):
        today = date.today()
        next_week = today + timedelta(days=7)
        birthdays = []
        for record in self.data.values():
            if record.birthday:
                birthday_this_year = record.birthday.value.replace(year=today.year)
                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)
                if today <= birthday_this_year < next_week:
                    adjusted_birthday = adjust_for_weekend(birthday_this_year)
                    birthdays.append(
                        {"name": record.name.value, "congratulation_date": adjusted_birthday.strftime("%Y.%m.%d")})
        return birthdays

def string_to_date(date_string):
    return datetime.strptime(date_string, "%Y.%m.%d").date()

def find_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days_ahead)

def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:  # Якщо субота або неділя
        return find_next_weekday(birthday, 0)  # Переносимо на наступний понеділок
    return birthday  # В іншому випадку повертаємо оригінальну дату

def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, IndexError) as e:
            return str(e)
    return wrapper

@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        return "Not enough arguments. Usage: add <name> <phone>"
    name = " ".join(args[:-1])
    phone = args[-1]
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    else:
        message = "Contact updated."

    if phone:
        try:
            record.add_phone(phone)
        except ValueError as e:
            return str(e)

    return message

@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 2:
        return "Not enough arguments. Usage: change <name> <phone>"
    name = " ".join(args[:-1])
    phone = args[-1]
    record = book.find(name)
    if record:
        old_phones = [p.value for p in record.phones]
        record.phones.clear()
        try:
            record.add_phone(phone)
        except ValueError as e:
            return str(e)
        return f"Phone number for {name} changed from {', '.join(old_phones)} to {phone}"
    return f"Contact {name} not found"

@input_error
def show_phone(args, book: AddressBook):
    if len(args) < 1:
        return "Not enough arguments. Usage: phone <name>"
    name = " ".join(args)
    record = book.find(name)
    if record:
        phones = [p.value for p in record.phones]
        if phones:
            return f"{name}'s phones: {', '.join(phones)}"
        return f"{name} has no phone numbers"
    return f"Contact {name} not found"

@input_error
def show_all(args, book: AddressBook):
    if book.data:
        result = "Address Book:\n"
        for record in book.data.values():
            result += str(record) + "\n"
        return result.strip()
    return "Address Book is empty"

@input_error
def add_birthday(args, book):
    if len(args) < 2:
        return "Not enough arguments. Usage: add-birthday <name> <birthday>"
    name = " ".join(args[:-1])
    birthday = args[-1]
    record = book.find(name)
    if record:
        try:
            record.add_birthday(birthday)
            return f"Birthday added for {name}"
        except ValueError as e:
            return str(e)
    return f"Contact {name} not found"

@input_error
def show_birthday(args, book):
    if len(args) < 1:
        return "Not enough arguments. Usage: show-birthday <name>"
    name = " ".join(args)
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday: {record.birthday.value}"
    elif record:
        return f"{name} has no birthday set"
    return f"Contact {name} not found"

@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if upcoming_birthdays:
        result = "Upcoming birthdays:\n"
        for record in upcoming_birthdays:
            result += f"{record['name']}: {record['congratulation_date']}\n"
        return result.strip()
    return "No upcoming birthdays"

def parse_input(input_str):
    parts = input_str.strip().split()
    command = parts[0].lower() if parts else ""
    args = parts[1:]
    return command, args

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

def main():
    book = load_data()

    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
