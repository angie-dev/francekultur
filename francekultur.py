#!/usr/bin/env python3
#
# Copyright 2018 Cécile Ritte
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import parse
import argparse
import requests
import subprocess
import logging
from bs4 import BeautifulSoup

from html.parser import HTMLParser
try:
    from HTMLParser import HTMLParseError
except ImportError as e:
    # HTMLParseError is removed in Python 3.5. Since it can never be
    # thrown in 3.5, we can just define our own class as a placeholder.
    class HTMLParseError(Exception):
        pass


def handle_download(args):
    url = args.url

    # TODO : fix url[0]
    primary_podcast = get_podcasts_from_page(url[0])

    download(primary_podcast)

def get_podcasts_from_page(url):

    r1 = parse.parse("https://www.franceculture.fr/emissions/{restofurl}",url)
    if r1 == None:
        logger.error("Well, this is not a valid HTTPS franceculture URL...")
        sys.exit(1)

    session = requests.Session()
    session.max_redirects = 3
    session.timeout = 5

    try:
        req = requests.get(url, timeout=3);
        req.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logger.error("Http Error:",err)
        sys.exit(1)
    except requests.exceptions.ConnectionError as errc:
        logger.error("Error Connecting:",errc)
        sys.exit(1)
    except requests.exceptions.Timeout as errt:
        logger.error("Timeout Error:",errt)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        logger.error("Exception when fetching page content : ",err)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.error("Program was interrupted by user")
        sys.exit(1)
    finally:
        try:
            soup = BeautifulSoup(req.text, "html.parser")
        except SyntaxError as se:
            logger.error("Check your BeautifulSoup version : {0}".format(se))
            sys.exit(1)
        except ImportError as ie:
            logger.error("Check your BeautifulSoup version or that it is installed : {0}".format(ie))
            sys.exit(1)
        except Exception as e:
            logger.error("Some exception occured : {0}".format(e))
            sys.exit(1)

        try:
            logger.info("Parsing page : {0}".format(soup.title.string))
        except logger.exceptions.Exception as err:
            logger.warning('Seems there was an issue printing page title, might indicate further problems: {0}'.format(err))
            #continue

        try:
            primary_podcast_el = soup.find(class_="heading-zone-player-button").find('button', class_="replay-button")

            if primary_podcast_el == None:
                logger.error("Could not find primary podcast, exiting...")
                sys.exit(1)

            if primary_podcast_el.has_attr("disabled"):
                logger.error("This podcast is not playable on the site, exiting...")
                sys.exit(1)

            if not primary_podcast_el.has_attr("data-asset-source"):
                logger.error("Could not find data source, exiting...")
                sys.exit(1)

            primary_podcast_link = primary_podcast_el.attrs['data-asset-source']
            r2 = parse.parse("https://{path}/{technical_name}.mp3", primary_podcast_link)
            if r2 == None:
                logger.error("Could not validate mp3 link, existing...")
                sys.exit(1)
            else:        
                primary_podcast_name = primary_podcast_el.attrs['data-title-link'].split("/")[-1]
                if len(primary_podcast_name) > 255: primary_podcast_name = technical_name
                logger.info("Found primary podcast link : {0} for {1}".format(primary_podcast_link, primary_podcast_name))
        except HTMLParseError as err:
            logger.error("Error parsing HTML : {0}".format(err))
            sys.exit(1)
        except Exception as e:
            logger.error("Some exception occured : {0}".format(e))
            sys.exit(1)

    primary_podcast = {'title': primary_podcast_name, 'link': primary_podcast_link}

    return primary_podcast

def download(podcast):
    
    file_name = podcast['title']+'.mp3'
    file_link = podcast['link']

    print(file_name)
    try:
        process = subprocess.run(['wget','-nv','--show-progress', '-O', file_name, file_link])
    except OSError as err:
        if err.errno == os.errno.ENOENT:
            logger.warning("Could not find wget, please install wget : {0}".format(err))
        else:
            logger.error("Some unknown issue {1} occurred with wget: {0}".format(err, err.errno))
    except KeyboardInterrupt as err:
        logger.error("Download interrupted by user: {0}".format(err))
    except subprocess.SubprocessError as err:
        logger.error(err)
        sys.exit(1)
    
    try:
        logger.debug("Wget video terminated with {0}".format(process.returncode))
    except UnboundLocalError:
        logger.warning("Couldn't retrieve wget return code, probably due to KeyboardInterrupt, continuing program")

def arg_parser():
    parser = argparse.ArgumentParser("Utility to download france culture podcasts",formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-v', '--verbose', action='count', help='define console verbosity up to vvv')
    parser.add_argument('url', nargs=1, help='the URL(s) of the page where the podcast can be streamed')
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)
    
    return args

def init_logger(args):
    logger = logging.getLogger('francekultur.py')
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter( logging.Formatter('[%(levelname)s] %(message)s') )

    logger.addHandler(console_handler)

    if not args.verbose:
        console_handler.setLevel('ERROR')
    elif args.verbose == 1:
        console_handler.setLevel('WARNING')
    elif args.verbose == 2:
        console_handler.setLevel('INFO')
    elif args.verbose >= 3:
        console_handler.setLevel('DEBUG')
    else:
        logger.warning("Wrong verbosity, will default to ERROR")
        console_handler.setLevel('ERROR')

    return logger

if __name__ == '__main__':
    args = arg_parser()
    
    logger = init_logger(args)

    logger.info(args)

    handle_download(args)
