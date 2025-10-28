import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_vacancies_for_language_from_sj(language, secret_key):
    """Получение вакансий по указанному языку программирования."""
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': secret_key}
    payload = {
        'period': 30,
        'town': 4,
        'catalogues': 48,
        'keyword': language,
        'no_agreement': 1
    }
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_sj(vacancy):
    """Прогнозирует ожидаемую зарплату из вакансии."""
    if vacancy['currency'] != 'rub':
        return None

    elif vacancy['payment_from'] and vacancy['payment_to']:
        expected_salary = (vacancy['payment_from'] + vacancy['payment_to']) / 2

    elif vacancy['payment_from']:
        expected_salary = vacancy['payment_from'] * 1.2

    elif vacancy['payment_to']:
        expected_salary = vacancy['payment_to'] * 0.8

    return expected_salary


def collect_information_form_sj(languages, secret_key):
    """Сбор информации с сайта 'SuperJob'."""
    languages_info = {}

    for language in languages:
        language_data = get_vacancies_for_language_from_sj(language, secret_key)
        all_salaries = []

        for vacancy in language_data['objects']:
            salary = predict_rub_salary_sj(vacancy)
            if salary != None:
                all_salaries.append(salary)

        average_salary_for_language = int(sum(all_salaries) / len(all_salaries))

        languages_info[language] = {
            'vacancies_found': language_data['total'],
            'vacancies_processed': len(all_salaries),
            'average_salary': average_salary_for_language,
        }

    return languages_info


def get_vacancies_for_language_from_hh(language, page=0):
    """Получение вакансий по указанному языку программирования."""
    url = 'https://api.hh.ru/vacancies'
    payload = {
        'page': page,
        'professional_role': '96',
        'area': '1',
        'period': 30,
        'text': language,
        'only_with_salary': True,
    }
    response = requests.get(url, params=payload)
    response.raise_for_status()
    return response.json()


def predict_rub_salary_hh(vacancy):
    """Прогнозирует ожидаемую зарплату из вакансии."""
    if vacancy['salary']['currency'] != 'RUR':
        return None

    elif vacancy['salary']['from'] and vacancy['salary']['to']:
        expected_salary = (vacancy['salary']['from'] + vacancy['salary']['to']) / 2

    elif vacancy['salary']['from']:
        expected_salary = vacancy['salary']['from'] * 1.2

    elif vacancy['salary']['to']:
        expected_salary = vacancy['salary']['to'] * 0.8

    return expected_salary


def collect_information_from_hh(languages):
    """Сбор информации с сайта 'HeadHunter'."""
    languages_info = {}

    for language in languages:
        language_data = get_vacancies_for_language_from_hh(language)
        vacancies_found = language_data['found']
        pages_number = language_data['pages']

        page = 0
        all_salaries = []

        while page <= pages_number:
            response = get_vacancies_for_language_from_hh(language, page)

            for vacancy in response['items']:
                salary = predict_rub_salary_hh(vacancy)
                if salary != None:
                    all_salaries.append(salary)
            
            page += 1

        average_salary_for_language = int(sum(all_salaries) / len(all_salaries))

        languages_info[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': len(all_salaries),
            'average_salary': average_salary_for_language
        }

    return languages_info


def show_table_by_language(title, languages_info):
    table_data = [
        [
            'Язык программирования',
            'Средняя зарплата',
            'Найдено вакансий',
            'Обработано вакансий',
        ]
    ]

    for language, stats in languages_info.items():
        row = [
            language,
            stats['average_salary'],
            stats['vacancies_found'],
            stats['vacancies_processed'],
        ]
        table_data.append(row)

    table = AsciiTable(table_data, title)
    print(table.table)


def main():
    load_dotenv()
    sj_secret_key = os.environ['SJ_SECRET_KEY']
    languages = ['Python', 'Java', 'Javascript']

    languages_info_from_hh = collect_information_from_hh(languages)
    languages_info_from_sj = collect_information_form_sj(languages, sj_secret_key)
    show_table_by_language('HeadHunter Moscow', languages_info_from_hh)
    print()
    show_table_by_language('SuperJob Moscow', languages_info_from_sj)


if __name__=='__main__':
    main()