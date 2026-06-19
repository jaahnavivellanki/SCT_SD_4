import logging
from src.gui import MainWindow

def run_app():
    """
    Initialize global setups like logging and trigger the CustomTkinter UI.
    """
    # Configure logging formatting and output level
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Initializing Product Scraper Pro...")
    
    # Launch main application window
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    run_app()
