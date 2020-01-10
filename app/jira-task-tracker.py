#!/usr/bin/python
"""
Grabs the current weeks tickets for the given user.
"""
import os
import argparse
from tabulate import tabulate

import jira
from jira.client import JIRA


RESET="\033[0m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW='\033[93m'
BLUE="\033[34m"


def retreive_argparse_arguments():
    """Retreives the argparse object for command line arguments.

    Returns:
        arguments: argparse object of command line arguments.
                   RuntimeError otherwise.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user", action="store", help="User to retrieve tickets.")
    parser.add_argument('-d','--days', default=7, type=int,
                        help='The number of days to look back (7, 14, ...)', nargs='?')
    parser.add_argument('-m','--max-results', default=100, type=int,
                        help='Max results to log (100)', nargs='?')
    parser.add_argument('-s','--sort-by', default='ticket', type=str,
                        help="Sort tickets by : ('ticket', 'summary', 'status', 'interacted')", nargs='?')

    arguments = parser.parse_args()

    return arguments


def create_jira_session():
    """
    """

    jira_server = os.environ.get('JIRA_SERVER', '')
    basic_auth = os.environ.get('JIRA_AUTH', '')
    certificate = os.environ.get('JIRA_CERT', '')
    options = {'verify': certificate}

    return JIRA(jira_server, basic_auth=basic_auth, options=options)


def get_user_tickets_in_range(session, user, days, max_results):
    """
    """

    query = "assignee = {0} and updated >=  -{1}d order by key".format(user, days)

    return session.search_issues(query, maxResults=max_results)


def get_ticket_comments(ticket, session):
    """
    """

    return session.comments(ticket)


def has_user_commented(ticket, session, user):
    """
    """

    comments = get_ticket_comments(ticket, session)
    authors = [comment.author.name for comment in comments]
    if user in authors:
        return 'Yes'
    return 'No'


def get_ticket_data(session, ticket, user):
    """
    """

    name = ticket.key
    summary = ticket.fields.summary
    status = ticket.fields.status.name
    commented = has_user_commented(ticket, session, user)

    return name, summary, status, commented


def get_active_tickets(session, user, days, max_results):
    """
    """

    assigned_tickets = get_user_tickets_in_range(session,
                                                 user,
                                                 days,
                                                 max_results)
    interacted_tickets = []
    for ticket in assigned_tickets:
        name, summary, status, commented = get_ticket_data(session,
                                                           ticket,
                                                           user)
        interacted_tickets.append([name, summary, status, commented])

    return interacted_tickets


def color_text(text):
    """
    """

    if not text:
        return []

    green_keys = ["done", "cancelled"]
    yellow_keys = ["in progress", "awaiting feedback", "in review"]
    red_keys = ["to do", "on hold"]

    out = []
    if text[-2].lower() in green_keys:
        for t in text:
            out.append(GREEN+t+RESET)
        return out
    elif text[-2].lower() in yellow_keys:
        for t in text:
            out.append(YELLOW+t+RESET)
        return out
    elif text[-2].lower() in red_keys:
        for t in text:
            out.append(RED+t+RESET)
        return out

    return text


def clean_row_data(data):
    """
    """

    out = []
    for table in data:
        out.append(color_text([i for i in table]))
    return out


def track_tickets(session, user, days, max_results, sort_by):
    """
    """

    headers = {'ticket': 0,
               'summary': 1,
               'status': 2,
               'interacted': 3}

    sort_idx = headers[sort_by.lower()]

    active_tickets = get_active_tickets(session,
                                        user,
                                        days,
                                        max_results)

    table = tabulate(
        clean_row_data( sorted(active_tickets, key=lambda x: x[sort_idx])),
        headers=['Ticket', 'Summary', 'Status', 'Interacted']
        )

    print "\n"
    print table
    print "\nUser {0} worked on {1} tickets in the last {2} days.".format(user, len(active_tickets), days)


def main():
    """
    """

    arguments = retreive_argparse_arguments()
    session = create_jira_session()

    track_tickets(session,
                  arguments.user,
                  arguments.days,                                        arguments.max_results,
                  arguments.sort_by)


if __name__ == "__main__":
    main()
