import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lib.models import Base, JBSession, JBTurn, JBUser, JBBot, JBMessage, JBDocumentStoreLog, JBQALog, JBApiLogger
import os
from dotenv import load_dotenv

load_dotenv('.env-dev')

db_name = os.getenv("POSTGRES_DATABASE_NAME")
db_user = os.getenv("POSTGRES_DATABASE_USERNAME")
db_password = os.getenv("POSTGRES_DATABASE_PASSWORD")
db_host = os.getenv("POSTGRES_DATABASE_HOST") # localhost for local upload of data
db_port = os.getenv("POSTGRES_DATABASE_PORT")

# Construct the SQLAlchemy connection URL using URL class
DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL)

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()


# To add it into sql file (one time setup for dev purpose)
def create_jb_user(*, pid, bot_id, first_name, last_name, phone_number, language_preference):
    new_user = JBUser(id=pid, bot_id=bot_id, first_name=first_name, last_name=last_name, phone_number=phone_number, language_preference=language_preference)
    session.add(new_user)
    session.commit()


def create_jb_bot(*, bot_id, name, phone_number):
    new_bot = JBBot(id=bot_id, name=name, phone_number=phone_number)
    session.add(new_bot)
    session.commit()


def create_jb_message(*, msg_id, user_created_at, session_id, channel_id, bot_id, media_type, media_url, user_text, channel, is_valid_message_type):
    new_message = JBMessage(id=msg_id, session_id=session_id, bot_id=bot_id, user_created_at=user_created_at, media_type=media_type, media_url=media_url, user_text=user_text, channel=channel, channel_id=channel_id, is_valid_message_type=is_valid_message_type)
    session.add(new_message)
    session.commit()

def create_jb_turn(*, turn_id, session_id, bot_id, turn_type, channel):
    new_turn = JBTurn(id=turn_id, session_id=session_id, bot_id=bot_id, turn_type=turn_type, channel=channel)
    session.add(new_turn)
    session.commit()

def create_jb_session(*, session_id, pid, bot_id):
    new_session = JBSession(id=session_id, pid=pid, bot_id=bot_id)
    session.add(new_session)
    session.commit()

def create_jb_api_logger(*, msg_id, user_id, turn_id, session_id, status):
    new_api_log = JBApiLogger(msg_id=msg_id, user_id=user_id, turn_id=turn_id, session_id=session_id, status=status)
    session.add(new_api_log)
    session.commit()

# For testing, to add sample data
def create_jb_document_store_log(bot_id, uuid, documents_list, total_file_size, status_code, status_message):
    doc_log = JBDocumentStoreLog(bot_id=bot_id, uuid=uuid, documents_list=documents_list, total_file_size=total_file_size, status_code=status_code, status_message=status_message)
    session.add(doc_log)
    session.commit()


# For testing, to add sample data
def create_jb_qa_log(id, pid, bot_id, document_uuid, input_language, query, audio_input_link, response, audio_output_link, retrieval_k_value, retrieved_chunks, prompt, gpt_model_name, status_code, status_message, response_time):
    qa_log = JBQALog(id=id, pid=pid, bot_id=bot_id, document_uuid=document_uuid, input_language=input_language, query=query, audio_input_link=audio_input_link, response=response, audio_output_link=audio_output_link, retrieval_k_value=retrieval_k_value, retrieved_chunks=retrieved_chunks, prompt=prompt, gpt_model_name=gpt_model_name, status_code=status_code, status_message=status_message, response_time=response_time)
    session.add(qa_log)
    session.commit()


# Sample insertions
# create_jb_user(pid='KanakHindi0', bot_id='bot0', first_name='Kanak', last_name='Hindi', phone_number='9876543210', language_preference='hi')
# create_jb_bot(bot_id='bot0', name='Nyaaya Setu', phone_number='9876543210')
# create_jb_bot("8d9de322-c0c0-44de-9054-76363e526831", "Nyaaya Setu", "9876553210")
# create_jb_message("89e77a12-9b70-418e-80b9-1d8f8b4d8d5e", "2024-01-19 17:21:25.953 +0530", "8d9de322-c0c0-44de-9054-76363e526830", 
#                   "voice", "https://jbmanager.blob.core.windows.net/jbfiles/input/89e77a12-9b70-418e-80b9-1d8f8b4d8d5e.ogg?st=2024-01-19T11%3A08%3A57Z&se=2024-02-18T11%3A09%3A57Z&sp=r&sv=2023-11-03&sr=b&sig=M7u92PtR1Xc/2CMEoM4iF9j7vzHIKmbyNAm6EIFfUk8%3D", 
#                   "", "wa", True)
# create_jb_message(msg_id='msg0', user_created_at='2024-01-19 17:21:25.953 +0530', session_id='session0', channel_id='channel0', bot_id='bot0', media_type='text', media_url='', user_text='तुम कैसे हो', channel='wa', is_valid_message_type=True)
# create_jb_message(msg_id='msg1', user_created_at='2024-01-19 17:21:25.953 +0530', session_id='session0', channel_id='channel0', bot_id='bot0', media_type='voice', media_url='', user_text='तुम कैसे हो', channel='wa', is_valid_message_type=True)
# create_jb_message(msg_id='msg2', user_created_at='2024-01-19 17:21:25.953 +0530', session_id='session0', channel_id='channel0', bot_id='bot0', media_type='text', media_url='', user_text='प्यार क्या है?', channel='wa', is_valid_message_type=True)
# create_jb_message(msg_id='msg3', user_created_at='2024-01-19 17:21:25.953 +0530', session_id='session0', channel_id='channel0', bot_id='bot0', media_type='text', media_url='', user_text='book', channel='wa', is_valid_message_type=True)
# create_jb_message(msg_id='msg4', user_created_at='2024-01-19 17:21:25.953 +0530', session_id='session0', channel_id='channel0', bot_id='bot0', media_type='text', media_url='', user_text='9876543210', channel='wa', is_valid_message_type=True)
# create_jb_message(msg_id='msg5', user_created_at='2024-01-19 17:21:25.953 +0530', session_id='session0', channel_id='channel0', bot_id='bot0', media_type='text', media_url='', user_text='Microsoft1234', channel='wa', is_valid_message_type=True)
# create_jb_message(msg_id='msg6', user_created_at='2024-01-19 17:21:25.953 +0530', session_id='session0', channel_id='channel0', bot_id='bot0', media_type='text', media_url='', user_text='2', channel='wa', is_valid_message_type=True)
# create_jb_message(msg_id='msg7', user_created_at='2024-01-19 17:21:25.953 +0530', session_id='session0', channel_id='channel0', bot_id='bot0', media_type='text', media_url='', user_text='2345', channel='wa', is_valid_message_type=True)
create_jb_turn(turn_id='30573d73-a8c0-4cec-9901-da61846f5ce3', session_id='dc6a9c2a-7a0b-40d2-801c-d6628599a9ce', bot_id='123', turn_type='audio', channel='WA')

# create_jb_session(session_id='session0', pid='KanakHindi0', bot_id='bot0')
# create_jb_document_store_log("8d9de322-c0c0-44de-9054-76363e526831", "8d9de322-c0c0-44de-9054-76363e526832", ['a.xlsx', 'b.xlsx'], 27, 200, 'Success')
# create_jb_qa_log("8d9de322-c0c0-44de-9054-76363e526834", "8d9de322-c0c0-44de-9054-76363e526830", "8d9de322-c0c0-44de-9054-76363e526831", "8d9de322-c0c0-44de-9054-76363e526832"
#                  , "en", "", "https://jbmanager.blob.core.windows.net/jbfiles/input/89e77a12-9b70-418e-80b9-1d8f8b4d8d5e.ogg?st=2024-01-19T11%3A08%3A57Z&se=2024-02-18T11%3A09%3A57Z&sp=r&sv=2023-11-03&sr=b&sig=M7u92PtR1Xc/2CMEoM4iF9j7vzHIKmbyNAm6EIFfUk8%3D"
#                  , "test response", "https://jbmanager.blob.core.windows.net/jbfiles/input/89e77a12-9b70-418e-80b9-1d8f8b4d8d5e.ogg?st=2024-01-19T11%3A08%3A57Z&se=2024-02-18T11%3A09%3A57Z&sp=r&sv=2023-11-03&sr=b&sig=M7u92PtR1Xc/2CMEoM4iF9j7vzHIKmbyNAm6EIFfUk8%3D"
#                  , 5, "['The', 'The']", "you are a legal expert", "gpt4", 200, "Success", 1)