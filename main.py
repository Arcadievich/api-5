import requests
import os
import time
from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_vacancies_for_language_from_sj(language, secret_key, page=0):
    """Получение вакансий по указанному языку программирования."""
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': secret_key}

    vacancy_publication_period = 30
    town_index = 4
    professional_industry_index = 48
    count_per_page = 20

    payload = {
        'period': vacancy_publication_period,
        'town': town_index,
        'catalogues': professional_industry_index,
        'keyword': language,
        'no_agreement': 1,
        'page': page,
        'count': count_per_page,
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


def collect_salaries_by_language_form_sj(languages, secret_key):
    """Сбор информации с сайта 'SuperJob'."""
    languages_salaries = {}

    for language in languages:
        
        all_salaries = []
        all_vacancies = []
        max_vacancies = 1
        page = 0

        while len(all_vacancies) < max_vacancies:
            language_vacancies = get_vacancies_for_language_from_sj(
                language,
                secret_key,
                page,
            )

            all_vacancies.extend(language_vacancies.get("objects", []))

            for vacancy in language_vacancies['objects']:
                salary = predict_rub_salary_sj(vacancy)
                if salary:
                    all_salaries.append(salary)

            max_vacancies = language_vacancies['total']
            page += 1
            time.sleep(0.5)

        try:
            average_salary_for_language = int(sum(all_salaries) / len(all_salaries))
        except ZeroDivisionError:
            average_salary_for_language = 0

        languages_salaries[language] = {
            'vacancies_found': language_vacancies['total'],
            'vacancies_processed': len(all_salaries),
            'average_salary': average_salary_for_language,
        }

    return languages_salaries


def get_vacancies_for_language_from_hh(language, page=0):
    """Получение вакансий по указанному языку программирования."""
    url = 'https://api.hh.ru/vacancies'

    vacancy_publication_period = 30
    profession_index = '96'
    town_index = '1'

    payload = {
        'page': page,
        'professional_role': profession_index,
        'area': town_index,
        'period': vacancy_publication_period,
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


def collect_salaries_by_language_from_hh(languages):
    """Сбор информации с сайта 'HeadHunter'."""
    languages_salaries = {}

    for language in languages:
        page, pages_number, vacancies_found = 0, 0, 0
        all_salaries = []

        while page <= pages_number:
            response = get_vacancies_for_language_from_hh(language, page)

            for vacancy in response['items']:
                salary = predict_rub_salary_hh(vacancy)
                if salary:
                    all_salaries.append(salary)
            
            pages_number = response['pages']
            vacancies_found = response['found']
            page += 1
            time.sleep(0.5)

        average_salary_for_language = int(sum(all_salaries) / len(all_salaries))

        languages_salaries[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': len(all_salaries),
            'average_salary': average_salary_for_language
        }

    return languages_salaries


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

    languages_salaries_from_hh = collect_salaries_by_language_from_hh(languages)
    languages_salaries_from_sj = collect_salaries_by_language_form_sj(languages, sj_secret_key)

    show_table_by_language('HeadHunter Moscow', languages_salaries_from_hh)
    print()
    show_table_by_language('SuperJob Moscow', languages_salaries_from_sj)


if __name__=='__main__':
    main()