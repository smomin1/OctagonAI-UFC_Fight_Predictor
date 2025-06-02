from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import math
import re
from math import nan
import pandas as pd
import os
import json



def get_completed_event_urls():
    base_url = "http://ufcstats.com/statistics/events/completed?page=all"
    response = requests.get(base_url)

    if response.status_code != 200:
        raise Exception(f"Failed to load page, status code: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    event_links = []

    for a_tag in soup.select("a.b-link.b-link_style_black"):
        href = a_tag.get('href')
        if href and '/event-details/' in href:
            print(href)
            event_links.append(href)
    
    # Save to file
    with open('event_urls.txt', 'w') as f:
        for url in event_links:
            f.write(url + '\n')
    
    print(f"\nTotal events found: {len(event_links)} (saved to event_urls.txt)")
    return event_links


def get_fight_urls(event_urls):
    fight_urls = []

    for i, event_url in enumerate(event_urls, 1):
        try:
            response = requests.get(event_url)
            if response.status_code != 200:
                print(f" Failed to load event {event_url}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Each fight is in a row that links to fight details
            rows = soup.select('tr.b-fight-details__table-row__hover')
            for row in rows:
                link_tag = row.find('a', class_='b-flag b-flag_style_green')
                if link_tag:
                    href = link_tag.get('href')
                    if href and '/fight-details/' in href:
                        fight_urls.append(href)
                        print(href)

            print(f" Collected fights from event {i}/{len(event_urls)}")

        except Exception as e:
            print(f" Error scraping {event_url}: {e}")

    # Save fight URLs to file
    with open('fight_urls.txt', 'w') as f:
        for url in fight_urls:
            f.write(url + '\n')

    print(f"\nTotal fight URLs collected: {len(fight_urls)} (saved to fight_urls.txt)")
    return fight_urls


def get_fighter_urls(fight_urls):
    fighter_urls = []  # List to store the scraped data with the fighter stat pages

    num_of_urls = len(fight_urls) * 2
    i = 0

    # Iterating through each fight
    for url in fight_urls:
        # Access the page
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, 'html.parser')

            # Access all elements that contain links to the fighter's page
            fighters_urls_element = soup.find_all('a', class_='b-link b-fight-details__person-link')

            # Iterate through red and blue fighter
            for element in fighters_urls_element:
                fighter_url = element.get('href')
                fighter_urls.append(fighter_url)

                i += 1
                print(f'{i} out of {num_of_urls} fighter urls collected')

        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            return None

    print('Successfully collected urls for all fighters')
    print('The urls are saved in the fighter_urls.txt')

    with open('fighter_urls.txt', 'w') as file:
        for url in fighter_urls:
            file.write(url + "\n")

    return fighter_urls



def get_fighters_stats(fighter_urls):
    fighters_stats = []
    i = 0

    for fighter_url in fighter_urls:
        response = requests.get(fighter_url)

        if response.status_code == 200:
            print(fighter_url)

            soup = BeautifulSoup(response.text, 'html.parser')

            fighter_name = soup.find('span', class_='b-content__title-highlight').text.strip()
            fighter_record = soup.find('span', class_='b-content__title-record').text.replace('Record:', '').strip()
            fighter_record_values = fighter_record.split('-')
            fighter_wins = fighter_record_values[0]
            fighter_losses = fighter_record_values[1]
            fighter_draws = fighter_record_values[2] if len(fighter_record_values) > 2 else None

            fighter_stats_elements = soup.find_all('li', class_='b-list__box-list-item b-list__box-list-item_type_block')
            fighter_stats = [stat.get_text(strip=True) for stat in fighter_stats_elements]

            fighter_height = fighter_stats[0]
            if fighter_height != '--':
                height_match = re.match(r'Height:(\d+)\' (\d+)"', fighter_height)
                if height_match is not None:
                    feet, inches = map(int, height_match.groups())
                    height_in_cm = (feet * 30.48) + (inches * 2.54)
                else:
                    height_in_cm = nan
            else:
                height_in_cm = nan

            fighter_weight = fighter_stats[1]
            if fighter_weight != '--':
                weight_match = re.match(r'Weight:(\d+) lbs\.', fighter_weight)
                if weight_match:
                    weight_in_lbs = int(weight_match.group(1))
                    weight_in_kg = weight_in_lbs * 0.453592
                else:
                    weight_in_kg = nan
            else:
                weight_in_kg = nan

            fighter_reach = fighter_stats[2].replace('Reach:', '').strip()
            if fighter_reach != '--':
                reach_in_inch = fighter_reach.replace('"', '').strip()
                reach_in_cm = int(reach_in_inch) * 2.54
            else:
                reach_in_cm = nan

            fighter_dob = fighter_stats[4].replace('DOB:', '').strip()
            if fighter_dob != '--':
                dob = datetime.strptime(fighter_dob, '%b %d, %Y')
                current_date = datetime.now()
                fighter_age = current_date.year - dob.year - ((current_date.month, current_date.day) < (dob.month, dob.day))
            else:
                fighter_age = nan

            fighter_stance = fighter_stats[3].replace('STANCE:', '').strip()
            fighter_SLpM = fighter_stats[5].replace('SLpM:', '').strip()
            fighter_Str_Acc = fighter_stats[6].replace('Str. Acc.:', '').rstrip('%')
            fighter_SApM = fighter_stats[7].replace('SApM:', '').strip()
            fighter_Str_Def = fighter_stats[8].replace('Str. Def:', '').rstrip('%')
            fighter_TD_Avg = fighter_stats[10].replace('TD Avg.:', '').strip()
            fighter_TD_acc = fighter_stats[11].replace('TD Acc.:', '').rstrip('%')
            fighter_TD_def = fighter_stats[12].replace('TD Def.:', '').rstrip('%')
            fighter_Sub_Avg = fighter_stats[13].replace('Sub. Avg.:', '').strip()

            fighter_stats_dict = {
                'name': fighter_name,
                'wins': int(fighter_wins),
                'losses': int(fighter_losses),
                'height_cm': round(height_in_cm, 2) if not math.isnan(height_in_cm) else None,
                'weight_kg': round(weight_in_kg, 2) if not math.isnan(weight_in_kg) else None,
                'reach_cm': round(reach_in_cm, 2) if not math.isnan(reach_in_cm) else None,
                'stance': fighter_stance,
                'age': round(float(fighter_age)) if not math.isnan(float(fighter_age)) else None,
                'significant_strikes_landed_per_minute': float(fighter_SLpM),
                'significant_strike_accuracy': float(fighter_Str_Acc) / 100,
                'significant_strikes_absorbed_per_minute': float(fighter_SApM),
                'significant_strike_defense': float(fighter_Str_Def) / 100,
                'takedown_average': float(fighter_TD_Avg),
                'takedown_accuracy': float(fighter_TD_acc) / 100,
                'takedown_defense': float(fighter_TD_def) / 100,
                'submission_average': float(fighter_Sub_Avg),
            }

            fighters_stats.append(fighter_stats_dict)
            i += 1
            print(i, "out of", len(fighter_urls))

            # with open('fighters_stats.txt', 'a') as file:
            #     for key, value in fighter_stats_dict.items():
            #         file.write(f"{key}: {value}\n")
            #     file.write("\n")

            # Save to JSON at the end
            with open("fighters_stats.json", "w") as f:
                json.dump(fighters_stats, f, indent=2)

            print('Data has been saved to the file\n')
            print(fighter_stats_dict)

    return fighters_stats


def get_red_fighters_stats(fighters_stats):
    red_fighters_stats = []
    for index, fighter in enumerate(fighters_stats):
        if index % 2 == 0:  # Even index, red fighter
            red_fighters_stats.append(fighter)
    return red_fighters_stats

def get_blue_fighters_stats(fighters_stats):
    blue_fighters_stats = []
    for index, fighter in enumerate(fighters_stats):
        if index % 2 != 0:  # Odd index, blue fighter
            blue_fighters_stats.append(fighter)
    return blue_fighters_stats



def create_r_fighter_dicts(red_fighters_stats):
    red_fighter_dicts = []
    for red_fighter_stat in red_fighters_stats:
        red_fighter_dict = {
            'red_total_wins': red_fighter_stat['wins'],
            'red_total_losses': red_fighter_stat['losses'],
            'red_age': red_fighter_stat['age'],
            'red_height_cm': red_fighter_stat['height_cm'],
            'red_weight_kg': red_fighter_stat['weight_kg'],
            'red_reach_cm': red_fighter_stat['reach_cm'],
            'red_stance': red_fighter_stat['stance'],
            'red_significant_strikes_landed_per_minute': red_fighter_stat['significant_strikes_landed_per_minute'],
            'red_significant_strikes_absorbed_per_minute': red_fighter_stat['significant_strikes_absorbed_per_minute'],
            'red_significant_strike_accuracy': red_fighter_stat['significant_strike_accuracy'],
            'red_takedown_accuracy': red_fighter_stat['takedown_accuracy'],
            'red_significant_strike_defense': red_fighter_stat['significant_strike_defense'],
            'red_takedown_defense': red_fighter_stat['takedown_defense'],
            'red_submission_average': red_fighter_stat['submission_average'],
            'red_takedown_average': red_fighter_stat['takedown_average']
        }
        red_fighter_dicts.append(red_fighter_dict)
    return red_fighter_dicts


def create_b_fighter_dicts(blue_fighters_stats):
    blue_fighter_dicts = []
    for blue_fighter_stat in blue_fighters_stats:
        blue_fighter_dict = {
            'blue_total_wins': blue_fighter_stat['wins'],
            'blue_total_losses': blue_fighter_stat['losses'],
            'blue_age': blue_fighter_stat['age'],
            'blue_height_cm': blue_fighter_stat['height_cm'],
            'blue_weight_kg': blue_fighter_stat['weight_kg'],
            'blue_reach_cm': blue_fighter_stat['reach_cm'],
            'blue_stance': blue_fighter_stat['stance'],
            'blue_significant_strikes_landed_per_minute': blue_fighter_stat['significant_strikes_landed_per_minute'],
            'blue_significant_strikes_absorbed_per_minute': blue_fighter_stat['significant_strikes_absorbed_per_minute'],
            'blue_significant_strike_accuracy': blue_fighter_stat['significant_strike_accuracy'],
            'blue_takedown_accuracy': blue_fighter_stat['takedown_accuracy'],
            'blue_significant_strike_defense': blue_fighter_stat['significant_strike_defense'],
            'blue_takedown_defense': blue_fighter_stat['takedown_defense'],
            'blue_submission_average': blue_fighter_stat['submission_average'],
            'blue_takedown_average': blue_fighter_stat['takedown_average']
        }
        blue_fighter_dicts.append(blue_fighter_dict)
    return blue_fighter_dicts





def create_stats_dict(current_fight_stats):
    print("Length of current_fight_dict:", len(current_fight_stats))
    print("current_fight_dict:", current_fight_stats)

    if len(current_fight_stats) >= 11:
        # Red
        r_sig_str_values = current_fight_stats[4].split(' of ')
        r_total_str_values = current_fight_stats[8].split(' of ')
        r_td_values = current_fight_stats[10].split(' of ')

        try:
            r_str_acc = (int(r_total_str_values[0]) / int(r_total_str_values[1])) * 100 if r_total_str_values != '---' else 0
        except ZeroDivisionError:
            r_str_acc = 0

        r_ctrl_time = current_fight_stats[18]
        r_ctrl_time_sec = int(r_ctrl_time.split(':')[0]) * 60 + int(r_ctrl_time.split(':')[1]) if ':' in r_ctrl_time else 0

        # Blue
        b_sig_str_values = current_fight_stats[5].split(' of ')
        b_total_str_values = current_fight_stats[9].split(' of ')
        b_td_values = current_fight_stats[11].split(' of ')

        try:
            b_str_acc = (int(b_total_str_values[0]) / int(b_total_str_values[1])) * 100 if b_total_str_values != '---' else 0
        except ZeroDivisionError:
            b_str_acc = 0

        b_ctrl_time = current_fight_stats[19]
        b_ctrl_time_sec = int(b_ctrl_time.split(':')[0]) * 60 + int(b_ctrl_time.split(':')[1]) if ':' in b_ctrl_time else 0

        totals_dict = {
            # Red
            'red_fight_knockdowns': round(float(current_fight_stats[2])),
            'red_fight_significant_strikes_landed': round(float(r_sig_str_values[0])),
            'red_fight_significant_strikes_attempted': round(float(r_sig_str_values[1])),
            'red_fight_significant_strike_accuracy': float(current_fight_stats[6].rstrip('%')) / 100 if current_fight_stats[6] != '---' else 0,
            'red_fight_total_strikes_landed': round(float(r_total_str_values[0])),
            'red_fight_total_strikes_attempted': round(float(r_total_str_values[1])),
            'red_fight_total_strike_accuracy': round(r_str_acc) / 100 if r_str_acc != '---' else 0,
            'red_fight_takedowns_landed': round(float(r_td_values[0])),
            'red_fight_takedowns_attempted': round(float(r_td_values[1])),
            'red_fight_takedown_accuracy': float(current_fight_stats[12].rstrip('%')) / 100 if current_fight_stats[12] != '---' else 0,
            'red_fight_submission_attempts': round(float(current_fight_stats[14])),
            'red_fight_reversals': round(float(current_fight_stats[16])),
            'red_fight_control_time_seconds': r_ctrl_time_sec,

            # Blue
            'blue_fight_knockdowns': round(float(current_fight_stats[3])),
            'blue_fight_significant_strikes_landed': round(float(b_sig_str_values[0])),
            'blue_fight_significant_strikes_attempted': round(float(b_sig_str_values[1])),
            'blue_fight_significant_strike_accuracy': float(current_fight_stats[7].rstrip('%')) / 100 if current_fight_stats[7] != '---' else 0,
            'blue_fight_total_strikes_landed': round(float(b_total_str_values[0])),
            'blue_fight_total_strikes_attempted': round(float(b_total_str_values[1])),
            'blue_fight_total_strike_accuracy': round(b_str_acc) / 100 if b_str_acc != '---' else 0,
            'blue_fight_takedowns_landed': round(float(b_td_values[0])),
            'blue_fight_takedowns_attempted': round(float(b_td_values[1])),
            'blue_fight_takedown_accuracy': float(current_fight_stats[13].rstrip('%')) / 100 if current_fight_stats[13] != '---' else 0,
            'blue_fight_submission_attempts': round(float(current_fight_stats[15])),
            'blue_fight_reversals': round(float(current_fight_stats[17])),
            'blue_fight_control_time_seconds': b_ctrl_time_sec
        }

    else:
        totals_dict = {
            'red_fight_knockdowns': nan,
            'red_fight_significant_strikes_landed': nan,
            'red_fight_significant_strikes_attempted': nan,
            'red_fight_significant_strike_accuracy': nan,
            'red_fight_total_strikes_landed': nan,
            'red_fight_total_strikes_attempted': nan,
            'red_fight_total_strike_accuracy': nan,
            'red_fight_takedowns_landed': nan,
            'red_fight_takedowns_attempted': nan,
            'red_fight_takedown_accuracy': nan,
            'red_fight_submission_attempts': nan,
            'red_fight_reversals': nan,
            'red_fight_control_time_seconds': nan,

            'blue_fight_knockdowns': nan,
            'blue_fight_significant_strikes_landed': nan,
            'blue_fight_significant_strikes_attempted': nan,
            'blue_fight_significant_strike_accuracy': nan,
            'blue_fight_total_strikes_landed': nan,
            'blue_fight_total_strikes_attempted': nan,
            'blue_fight_total_strike_accuracy': nan,
            'blue_fight_takedowns_landed': nan,
            'blue_fight_takedowns_attempted': nan,
            'blue_fight_takedown_accuracy': nan,
            'blue_fight_submission_attempts': nan,
            'blue_fight_reversals': nan,
            'blue_fight_control_time_seconds': nan
        }


    return totals_dict


def create_common_dict(soup):
    # Get event name
    event_name = soup.find('h2', class_='b-content__title').text.strip()

    # Get fighter names
    fighter_tags = soup.find_all('h3', class_='b-fight-details__person-name')
    fighter_names = [fighter.get_text(strip=True) for fighter in fighter_tags]

    # Get WIN/LOSE status
    status_tags = soup.find_all('i', class_='b-fight-details__person-status')
    fighter_statuses = [s.get_text(strip=True) for s in status_tags]

    # Determine winner
    if fighter_statuses[0] == 'W':
        winner = 'Red'
    elif fighter_statuses[1] == 'W':
        winner = 'Blue'
    else:
        winner = 'Draw'

    # Fight title and weight class
    fight_title_tag = soup.find('i', class_='b-fight-details__fight-title')
    fight_title = fight_title_tag.text.strip() if fight_title_tag else ''
    weight_class = fight_title.split(' Bout')[0].strip() if ' Bout' in fight_title else fight_title.strip()

    # Fight result method
    method = soup.find('i', class_='b-fight-details__text-item_first').text.replace('Method:', '').strip()

    # Get general stats
    stat_tags = soup.find_all('i', class_='b-fight-details__text-item')
    fight_data = [stat.get_text(strip=True) for stat in stat_tags]

    # Is title bout
    is_title_bout = 1 if 'Title' in fight_title else 0

    # Gender
    gender = 'Women' if "Women's" in fight_title else 'Men'

    # Total number of rounds (from time format string)
    time_format_text = fight_data[2].replace('Time format:', '')
    round_match = re.search(r"(\d+)", time_format_text)
    total_rounds = int(round_match.group(1)) if round_match else None

    # Fight duration in seconds
    fight_time = fight_data[1].replace('Time:', '').strip()
    minutes, seconds = map(int, fight_time.split(':'))
    fight_duration_seconds = minutes * 60 + seconds

    # Referee name
    referee = fight_data[3].replace('Referee:', '').strip()

    # Final common dict
    common_dict = {
        'event_name': str(event_name),
        'red_fighter_name': fighter_names[0],
        'blue_fighter_name': fighter_names[1],
        'winner': winner,
        'weight_class': weight_class,
        'is_title_bout': is_title_bout,
        'gender': gender,
        'method': method,
        'finish_round': int(fight_data[0].replace('Round:', '').strip()),
        'total_rounds': total_rounds,
        'fight_duration_seconds': fight_duration_seconds,
        'referee_name': referee
    }

    return common_dict





def get_fight_data(fight_urls):
    all_fight_data = []  # List to store the full scraped fight data

    for index, fight_url in enumerate(fight_urls):
        print(f'Processing {index+1}/{len(fight_urls)}: {fight_url}')

        response = requests.get(fight_url)
        if response.status_code != 200:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract shared/common fight details (event, fighters, outcome, etc.)
        common_dict = create_common_dict(soup)

        # Extract statistical data from "Totals" section of the fight
        stats_data = []
        stats_tags = soup.find_all('p', class_='b-fight-details__table-text')
        for s in stats_tags:
            stat = s.text.strip()
            stats_data.append(stat)

        # Get the 'totals' stats (first 20 elements)
        if stats_data:
            current_fight_stats = stats_data[0:20]
        else:
            current_fight_stats = []

        # Build totals_dict based on available data
        totals_dict = create_stats_dict(current_fight_stats)

        # Combine and store result
        full_fight_dict = {**common_dict, **totals_dict}
        all_fight_data.append(full_fight_dict)


    # Save data to JSON file
    with open("fight_data.json", "w") as f:
        json.dump(all_fight_data, f, indent=2)

    print(f" Saved {len(all_fight_data)} fights to fight_data.json")


    return all_fight_data





def combine_fight_and_personal_stats(total_page_dicts, red_fighters_dicts, blue_fighters_dicts):
    # Convert dictionaries to DataFrames
    total_fight_stats_df = pd.DataFrame(total_page_dicts)
    red_fighters_df = pd.DataFrame(red_fighters_dicts)
    blue_fighters_df = pd.DataFrame(blue_fighters_dicts)

    # Define index columns for splitting
    red_split_column = 'r_ctrl_sec'  # Previously 'r_ctrl'
    blue_split_column = 'b_ctrl_sec'  # Previously 'b_ctrl'
    red_split_index = 24
    blue_split_index = 14

    # Split total fight stats into red-related, blue-related, and diff portions
    red_stats_df = total_fight_stats_df.iloc[:, :red_split_index + 1]
    blue_and_diff_df = total_fight_stats_df.iloc[:, red_split_index + 1:]

    blue_stats_df = blue_and_diff_df.iloc[:, :blue_split_index + 1]
    diff_stats_df = blue_and_diff_df.iloc[:, blue_split_index + 1:]

    # Combine all parts horizontally
    red_combined_df = pd.concat([red_stats_df, red_fighters_df], axis=1)
    blue_combined_df = pd.concat([blue_stats_df, blue_fighters_df], axis=1)
    final_combined_df = pd.concat([red_combined_df, blue_combined_df, diff_stats_df], axis=1)

    return final_combined_df




def calculate_diff(df):
    # Columns where taking the difference makes logical sense
    columns_to_calculate_diff = [
        'fight_knockdowns',
        'fight_significant_strikes_landed', 'fight_significant_strikes_attempted', 'fight_significant_strike_accuracy',
        'fight_total_strikes_landed', 'fight_total_strikes_attempted', 'fight_total_strike_accuracy',
        'fight_takedowns_landed', 'fight_takedown_attempts', 'fight_takedown_accuracy',
        'fight_submission_attempts', 'fight_reversals', 'fight_control_time_seconds',

        'total_wins', 'total_losses',
        'age', 'height_cm', 'weight_kg', 'reach_cm',
        'significant_strikes_landed_per_minute', 'significant_strikes_absorbed_per_minute',
        'significant_strike_accuracy', 'takedown_accuracy',
        'significant_strike_defense', 'takedown_defense',
        'submission_average', 'takedown_average'
    ]

    for column in columns_to_calculate_diff:
        red_col = f'red_{column}'
        blue_col = f'blue_{column}'
        diff_col = f'{column}_difference'

        if red_col in df.columns and blue_col in df.columns:
            df[diff_col] = df[red_col] - df[blue_col]

    return df




def create_large_dataset(url_range=None):
     # Step 1: Get all URLs and stats
    # fight_urls = list(tqdm(get_fight_urls(url_range), desc="Collecting Fight URLs"))
    # fighter_urls = list(tqdm(get_fighter_urls(fight_urls), desc="Collecting Fighter URLs"))

     # === FIGHT URLS ===
    if os.path.exists("fight_urls.txt"):
        with open("fight_urls.txt", "r") as f:
            fight_urls = [line.strip() for line in f.readlines()]
        print(f" Loaded {len(fight_urls)} fight URLs from file.")
    else:
        fight_urls = list(tqdm(get_fight_urls(url_range), desc="Collecting Fight URLs"))
        with open("fight_urls.txt", "w") as f:
            for url in fight_urls:
                f.write(url + "\n")

    # === FIGHTER URLS ===
    if os.path.exists("fighter_urls.txt"):
        with open("fighter_urls.txt", "r") as f:
            fighter_urls = [line.strip() for line in f.readlines()]
        print(f" Loaded {len(fighter_urls)} fighter URLs from file.")
    else:
        fighter_urls = list(tqdm(get_fighter_urls(fight_urls), desc="Collecting Fighter URLs"))
        with open("fighter_urls.txt", "w") as f:
            for url in fighter_urls:
                f.write(url + "\n")


    if os.path.exists("fighters_stats.json"):
        with open("fighters_stats.json", "r") as f:
            fighters_stats = json.load(f)
        print(f" Loaded {len(fighters_stats)} fighter stats from JSON.")
    else:
        fighters_stats = list(tqdm(get_fighters_stats(fighter_urls), desc="Collecting Fighter Stats"))
        with open("fighters_stats.json", "w") as f:
            json.dump(fighters_stats, f, indent=2)
        print(f" Fighter stats collected and saved to JSON.")

    # Step 2: Split fighter stats into red and blue
    red_fighters_stats = get_red_fighters_stats(fighters_stats)
    blue_fighters_stats = get_blue_fighters_stats(fighters_stats)

    # Step 3: Create fighter dictionaries
    red_fighters_dicts = create_r_fighter_dicts(red_fighters_stats)
    blue_fighters_dicts = create_b_fighter_dicts(blue_fighters_stats)

    # Step 4: Scrape fight-specific stats
    if os.path.exists("fight_data.json"):
        with open('fight_data.json', 'r') as f:
            fight_data = json.load(f)

        # Define keys to rename (without prefix)
        fight_keys_to_rename = [
            'knockdowns',
            'significant_strikes_landed', 'significant_strikes_attempted', 'significant_strike_accuracy',
            'total_strikes_landed', 'total_strikes_attempted', 'total_strike_accuracy',
            'takedowns_landed', 'takedown_attempts', 'takedown_accuracy',
            'submission_attempts', 'reversals', 'control_time_seconds'
        ]

        # Rename the keys in each record
        for record in fight_data:
            for key in fight_keys_to_rename:
                red_old = f'red_{key}'
                red_new = f'red_fight_{key}'
                if red_old in record:
                    record[red_new] = record.pop(red_old)

                blue_old = f'blue_{key}'
                blue_new = f'blue_fight_{key}'
                if blue_old in record:
                    record[blue_new] = record.pop(blue_old)
        
        total_page_dicts = fight_data 

        print(" Loaded total_page_dicts from fight_data.json")
    else:
        total_page_dicts = list(tqdm(get_fight_data(fight_urls), desc="Collecting Fight Data"))
        with open("fight_data.json", "w") as f:
            json.dump(total_page_dicts, f, indent=2)
        print(" Saved total_page_dicts to fight_data.json")

    # Step 5: Combine fight and personal stats
    full_fight_data = combine_fight_and_personal_stats(total_page_dicts, red_fighters_dicts, blue_fighters_dicts)

    # Step 6: Add difference columns
    full_fight_data = calculate_diff(full_fight_data)

    # Step 7: Save dataset to CSV
    completed_events_large_df = pd.DataFrame(full_fight_data)
    completed_events_large_df.to_csv('completed_events_large.csv', index=False)

   

    print('Large dataset has been collected and saved to "completed_events_large.csv".')
   
    return completed_events_large_df


def main():
    event_urls = get_completed_event_urls()
    dataset = create_large_dataset(event_urls)
    print(" Dataset creation complete!")

if __name__ == "__main__":
    event_urls = get_completed_event_urls()
    dataset = create_large_dataset(event_urls)
    print(" Dataset creation complete!")
