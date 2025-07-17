# Indeed Job Scraper

A Python-based web scraper for extracting job listings from Indeed across multiple countries with advanced features like session persistence, detailed job information extraction, and anti-detection capabilities.

## ⚠️ Educational Purpose Only

This project is created for **educational and demonstration purposes only**. It is intended to showcase web scraping techniques, automation skills, and Python programming capabilities. 

**Please note:**
- This scraper may violate Indeed's Terms of Service
- Use responsibly and respect website policies
- Consider using official APIs when available
- This is for learning and portfolio demonstration only

## 🚀 Features

### Multi-Country Support
- **8 Countries**: Australia, India, United States, United Kingdom, Canada, Singapore, Germany, France
- **Easy Configuration**: Simple country code switching
- **Localized URLs**: Automatic domain selection

### Advanced Filtering
- **Date Filters**: Last 24 hours, 3 days, 7 days, 14 days, 30 days
- **Salary Filters**: Minimum salary requirements
- **Job Type Filters**: Full-time, part-time, contract
- **Location Targeting**: City, region, or country-wide

### Session Management
- **Persistent Sessions**: Saves login state across runs
- **Cookie Management**: Automatic cookie handling
- **Reduced Manual Login**: Login once, use multiple times

### Detailed Data Extraction
- **Basic Info**: Job title, company, location, salary
- **Detailed Info**: Full job descriptions, company insights
- **Additional Data**: Job requirements, benefits, company size
- **Structured Output**: Clean CSV and JSON formats

### Anti-Detection Features
- **Undetected Chrome**: Advanced browser automation
- **Random Delays**: Human-like interaction patterns
- **Error Handling**: Robust retry mechanisms
- **Stealth Mode**: Reduced detection probability

## 📦 Installation

### Prerequisites
- Python 3.7+
- Chrome browser
- ChromeDriver (auto-installed)

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/indeed-scraper.git
   cd indeed-scraper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the scraper**
   ```bash
   python indeed_scraper.py
   ```

## 🛠️ Configuration

### Country Settings
```python
# Edit the main() function in indeed_scraper.py
COUNTRY = 'IN'  # Options: AU, IN, US, UK, CA, SG, DE, FR
```

### Search Parameters
```python
JOB_TITLE = "data engineer"
LOCATION = "india"
DATE_POSTED = "last_14_days"  # Options: any, last_24_hours, last_3_days, last_7_days, last_14_days, last_30_days
```

### Supported Countries
| Code | Country | Indeed Domain |
|------|---------|---------------|
| AU   | Australia | au.indeed.com |
| IN   | India | in.indeed.com |
| US   | United States | indeed.com |
| UK   | United Kingdom | uk.indeed.com |
| CA   | Canada | ca.indeed.com |
| SG   | Singapore | sg.indeed.com |
| DE   | Germany | de.indeed.com |
| FR   | France | fr.indeed.com |

## 📊 Output

### Files Generated
- **JSON**: `indeed_[COUNTRY]_[JOB]_[LOCATION]_[DATE]_[TIMESTAMP].json`
- **CSV**: `indeed_[COUNTRY]_[JOB]_[LOCATION]_[DATE]_[TIMESTAMP].csv`

### Data Fields
- `title`: Job title
- `company`: Company name
- `location`: Job location
- `salary`: Salary information (when available)
- `url`: Job posting URL
- `job_id`: Unique job identifier
- `full_job_description`: Complete job description
- `profile_insights`: Company profile information
- `job_requirements`: Job requirements and qualifications
- `benefits`: Benefits information
- `company_size`: Company size information
- `scraped_at`: Timestamp of scraping
- `country`: Country of job posting
- `page_number`: Page number in search results
- `position_on_page`: Position on the page

## 🔧 Technical Details

### Architecture
- **Browser Automation**: Selenium with Undetected Chrome
- **Data Parsing**: BeautifulSoup4 for HTML parsing
- **Session Management**: Pickle-based session persistence
- **Error Handling**: Comprehensive retry mechanisms
- **Rate Limiting**: Random delays and human-like behavior

### Key Classes
- `IndeedScraper`: Main scraper class
- **Methods**:
  - `setup_driver()`: Browser initialization
  - `navigate_to_jobs()`: Search navigation
  - `extract_jobs_from_page()`: Job data extraction
  - `scrape_all_pages()`: Full scraping workflow
  - `save_results()`: Data export

### Anti-Detection Measures
- Undetected ChromeDriver
- Random user agents
- Human-like delays
- Session persistence
- Error recovery
- Rate limiting

## 📈 Usage Examples

### Basic Usage
```python
from indeed_scraper import IndeedScraper

scraper = IndeedScraper(country='IN', save_session=True)
jobs = scraper.scrape_all_pages(
    job_title="python developer",
    location="bangalore",
    date_posted="last_7_days"
)
```

### Advanced Usage
```python
scraper = IndeedScraper(country='US', save_session=True)
jobs = scraper.scrape_all_pages(
    job_title="software engineer",
    location="san francisco",
    date_posted="last_3_days",
    salary_min=80000,
    job_type="fulltime",
    max_pages=5
)
```

## 🚨 Limitations

### Technical Limitations
- **Detection Risk**: May be detected by anti-bot systems
- **Rate Limiting**: Subject to IP-based rate limiting
- **Cloudflare**: May encounter Cloudflare challenges
- **Manual Intervention**: May require manual login/CAPTCHA solving

### Legal Considerations
- **Terms of Service**: May violate Indeed's ToS
- **Rate Limits**: Respect website rate limits
- **Data Usage**: Consider data usage policies
- **Commercial Use**: Not recommended for commercial purposes

## 🔒 Best Practices

### Ethical Usage
- Use for educational purposes only
- Respect website terms of service
- Implement reasonable delays
- Don't overwhelm servers
- Consider official APIs first

### Technical Best Practices
- Monitor for IP blocking
- Use VPN/proxy for heavy usage
- Implement proper error handling
- Save data incrementally
- Regular code updates for selector changes

## 🛡️ Legal Disclaimer

This software is provided for educational and research purposes only. Users are responsible for complying with all applicable laws and website terms of service. The authors assume no responsibility for any misuse or legal consequences arising from the use of this software.

**Key Points:**
- This tool may violate Indeed's Terms of Service
- Web scraping laws vary by jurisdiction
- Use at your own risk
- Consider legal alternatives (APIs, partnerships)
- Respect robots.txt and rate limits

## 🤝 Contributing

Contributions are welcome for educational improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### Areas for Improvement
- Additional country support
- Better error handling
- More data fields
- Performance optimizations
- Code documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Selenium**: Web automation framework
- **Undetected ChromeDriver**: Anti-detection browser automation
- **BeautifulSoup**: HTML parsing library
- **Python Community**: For excellent libraries and support

## 📞 Contact

For questions about this educational project:
- **Purpose**: Educational demonstration only
- **Issues**: Use GitHub Issues for bugs/questions
- **Portfolio**: This project demonstrates web scraping skills

---

**Remember: This is for educational purposes only. Always respect website terms of service and applicable laws.**