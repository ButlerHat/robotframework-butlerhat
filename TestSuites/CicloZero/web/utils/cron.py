import os
import datetime
import croniter
import tempfile

def cron_to_natural_language(cron_format):
    # Create a croniter object with the provided format string
    cron = croniter.croniter(cron_format)

    # Get the next scheduled execution time as a datetime object
    next_execution = cron.get_next(datetime.datetime)

    # Format the datetime object as a natural language string
    natural_language_string = next_execution.strftime("At %H:%M on %d-%m-%Y.")

    # Get the next scheduled execution time after the first one
    next_execution = cron.get_next(datetime.datetime)

    # Format the datetime object as a natural language string
    natural_language_string += " Next at " + next_execution.strftime("At %H:%M on %d-%m-%Y.")

    return natural_language_string


def get_cron_jobs():
    # Retrieve the list of cron jobs from the system's crontab
    crontab_output = os.popen("crontab -l").read()
    crontab_lines = crontab_output.splitlines()

    # Filter out any empty lines or comments
    cron_jobs = []
    for line in crontab_lines:
        line = line.strip()
        if line and not line.startswith("#"):
            cron_jobs.append(line)

    return cron_jobs


def insert_cron_job(cron_format, command):
    # Check if the job is already present in the crontab
    cron_jobs = get_cron_jobs()
    if f"{cron_format} {command}" in cron_jobs:
        return False

    # Write the new crontab line to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write((f"{cron_format} {command}\n").encode())
    temp_file.flush()

    # Insert the new crontab line
    os.system(f"(crontab -l ; cat {temp_file.name}) | crontab -")

    # Clean up the temporary file
    os.unlink(temp_file.name)

    return True

def delete_cron_job(cron_format, command):
    # Check if the job is present in the crontab
    cron_jobs = get_cron_jobs()
    if f"{cron_format} {command}" not in cron_jobs:
        return False

    # Create a temporary file containing the current crontab
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    os.system("crontab -l > " + temp_file.name)

    # Remove the crontab line containing the job
    with open(temp_file.name, "r") as f:
        crontab_lines = f.readlines()
    with open(temp_file.name, "w") as f:
        for line in crontab_lines:
            if f"{cron_format} {command}" not in line:
                f.write(line)

    # Update the crontab with the new version
    os.system(f"crontab {temp_file.name}")

    # Clean up the temporary file
    os.unlink(temp_file.name)

    return True



# Example usage
if __name__ == "__main__":
    cron_format = "* * * * *"
    command = "touch /tmp/test_add.txt"
    is_created = insert_cron_job(cron_format, command)
    print(is_created)

    # job_to_delete = {"cron_format": "* * * * *", "command": "touch /tmp/test_add.txt"}
    # delete_cron_job(job_to_delete)

