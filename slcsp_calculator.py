import csv
from collections import defaultdict
import argparse
import logging

def read_csv(file_path):
    """Read a CSV file and return rows as a list of dictionaries."""
    try:
        with open(file_path, mode="r") as file:
            return list(csv.DictReader(file))
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        raise

def write_csv(file_path, rows, headers):
    """Write rows to a CSV file with the specified headers."""
    try:
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)
        logging.info(f"Output written to {file_path}")
    except Exception as e:
        logging.error(f"Error writing file {file_path}: {e}")
        raise

def parse_silver_plans(plans):
    """Filter silver plans and group rates by (state, rate_area)."""
    silver_plans = defaultdict(list)
    for plan in plans:
        if plan["metal_level"] == "Silver":
            key = (plan["state"], plan["rate_area"])
            silver_plans[key].append(float(plan["rate"]))
    # Sort rates for each key to make it easy to find the second lowest
    for key in silver_plans:
        silver_plans[key].sort()
    return silver_plans

def map_zip_to_rate_areas(zips):
    """Map ZIP codes to associated (state, rate_area)."""
    zip_to_rate_areas = defaultdict(set)
    for z in zips:
        key = z["zipcode"]
        value = (z["state"], z["rate_area"])
        zip_to_rate_areas[key].add(value)
    return zip_to_rate_areas

def calculate_slcsp(zipcodes, zip_to_rate_areas, silver_plans):
    """Calculate the SLCSP for each ZIP code."""
    results = []
    for zip_entry in zipcodes:
        zip_code = zip_entry["zipcode"]
        rate_areas = zip_to_rate_areas[zip_code]

        # Log ambiguous or missing rate areas
        if len(rate_areas) != 1:
            if len(rate_areas) > 1:
                logging.warning(f"Ambiguous rate areas for ZIP code {zip_code}.")
            else:
                logging.warning(f"No rate areas found for ZIP code {zip_code}.")
            results.append([zip_code, ""])
            continue

        # Extract the single rate area
        rate_area = next(iter(rate_areas))
        rates = silver_plans.get(rate_area, [])

        # If fewer than 2 rates, leave blank
        if len(rates) < 2:
            logging.warning(f"Insufficient rates for rate area {rate_area}.")
            results.append([zip_code, ""])
        else:
            results.append([zip_code, f"{rates[1]:.2f}"])  # Second lowest rate
    return results


def get_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Calculate SLCSP for ZIP codes.")
    parser.add_argument("--plans", required=True, help="Path to plans.csv")
    parser.add_argument("--zips", required=True, help="Path to zips.csv")
    parser.add_argument("--slcsp", required=True, help="Path to slcsp.csv")
    parser.add_argument("--output", required=True, help="Path to output file")
    return parser.parse_args()

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

    args = get_args()

    logging.info("Reading input files...")
    plans = read_csv(args.plans)
    zips = read_csv(args.zips)
    slcsp = read_csv(args.slcsp)

    logging.info("Processing data...")
    silver_plans = parse_silver_plans(plans)
    zip_to_rate_areas = map_zip_to_rate_areas(zips)
    slcsp_results = calculate_slcsp(slcsp, zip_to_rate_areas, silver_plans)

    logging.info("Writing output...")
    write_csv(args.output, slcsp_results, ["zipcode", "rate"])
    logging.info("Process completed successfully.")

if __name__ == "__main__":
    main()
