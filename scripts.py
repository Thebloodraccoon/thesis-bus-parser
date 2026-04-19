from thesis.parser.app.tasks import update_cities, run_scraper, update_currencies


def main():
    # update_currencies()
    # update_cities()

    target_site = "inbus"

    result_scraper = run_scraper(
        site_name=target_site,
        depth_from=8,
        depth_to=30,
        threads=10
    )
    print("Результат парсинга:")
    for res in result_scraper:
        print(res)


if __name__ == "__main__":
    main()