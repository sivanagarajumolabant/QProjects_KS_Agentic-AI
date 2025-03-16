from src.logging import logger
from src.exception.exception import ProjectException
import sys

from src.components.datatingestion import DataIngestion

from src.components.datatingestion import DataIngestionArtifact
from src.components.datatingestion import DataIngestionConfig


if __name__=="__main__":
    
    data_ingestion=DataIngestion()
    train_data, test_data = data_ingestion.initate_data_ingestion()
    




