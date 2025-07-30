import time

import openai

from backend.common.logging import logging
from config import config as server_config

logger = logging.getLogger(__name__)

# Set your API key
openai.api_key = server_config.OPENAI_API_KEY

logger.info("OpenAI API key configured for sensory profile assistant")

PROMPT = """
Review the uploaded PDF and create a summary that follows the same structure and depth as this example summary—including behavioral impacts, daily functional challenges, caregiver observations, and recommendations where applicable. Do not just summarize scores; relate sensory responses to daily routines, emotional regulation, play, social engagement, and caregiver concerns, as shown in the example below.

Use this example as a template for both structure and clinical richness:

Sabrina’s sensory processing abilities were assessed using the Toddler Sensory Profile™ 2, completed by his caregiver. Results revealed a multifaceted sensory profile with significant variability across sensory domains. While Sabrina demonstrated typical responses to visual and oral input, he exhibited markedly heightened sensitivity in auditory, tactile, and general processing areas. His profile reflects both increased sensitivity and reactivity to certain types of sensory input (particularly sounds, touch, and environmental change) and decreased responsiveness in others, contributing to challenges in regulation, transitions, and participation in daily activities.

In the General Processing section, Sabrina also scored in the “Much More Than Others” range. His caregiver described him as having an unpredictable sleeping and eating pattern, being easily awakened, and getting anxious in new situations. Additionally, he was noted to withdraw from situations and act in ways that interfere with family routines, including difficulty during transitions such as preparing to leave the house or sitting in a stroller, which often lead to tantrums and self-injurious behaviors like hitting himself. These behaviors reflect challenges with regulation and adaptability. Consistent routines, advanced preparation for transitions, and use of visual schedules or first-then boards may help increase his comfort and reduce resistance.

In the Auditory Processing domain, Sabrina scored in the “Much More Than Others” range, indicating heightened reactivity to auditory stimuli. His caregiver reported that he startles easily at common environmental noises, such as dogs barking or children shouting, and is often distracted in noisy settings. Sabrina was also noted to ignore sounds, including his caregiver’s voice, and takes longer to respond to his own name, which may be interpreted as missed auditory cues. These patterns suggest that sound is not only overstimulating for Sabrina but may also hinder social engagement and responsiveness during routine interactions. Providing a quiet, predictable auditory environment and using touch or visual cues to gain his attention may help facilitate participation and calmness.

In the Visual Processing domain, Sabrina’s responses fell in the “Just Like the Majority of Others” range. He enjoys looking at moving or spinning objects such as ceiling fans and toy wheels, is attracted to shiny objects and screens, and responds similarly to peers in bright or unpredictable lighting conditions. His consistent and typical visual responses may be considered a strength and used to increase attention, engagement, and motivation during therapeutic and daily tasks.

Sabrina’s Behavioral Responses associated with sensory processing were in the “Much More Than Others” range. His caregiver reported frequent tantrums, clinginess, and a need to be held to stay calm. He also becomes fussy or irritable in novel environments, and, when overstimulated, may exhibit behaviors that are difficult to soothe. These patterns align with sensory modulation difficulties and highlight how sensory experiences may contribute to emotional dysregulation. Caregiver strategies that emphasize co-regulation, sensory breaks, and use of preferred calming items (e.g., cups with lids, music player) may help promote stability and comfort.

In the Touch Processing domain, Sabrina scored in the “Much More Than Others” range. His caregiver shared that he becomes upset when having his nails trimmed, resists cuddling, and withdraws from contact with uncomfortable textures, such as rough or sticky surfaces (e.g., carpet or countertops). He also exhibits difficulty tolerating dressing routines, such as pulling at clothing or resisting garments being put on. These behaviors are consistent with tactile defensiveness, which can interfere with participation in self-care tasks and physical affection. Sensory-based desensitization activities, including play with soft textures and graded exposure to tactile input, may promote improved tolerance.

In the Movement Processing domain, Sabrina scored in the “More Than Others” range. He shows a strong interest in movement-based activities, including bouncing, being held high in the air, swinging, rocking, and car rides. However, he also exhibits sensitivity to certain movement situations, such as becoming upset when placed on his back during diaper changes and appearing clumsy or accident-prone. These mixed responses to movement suggest both sensory-seeking and avoidant behaviors. Incorporating calming and organizing movement experiences—like slow swinging or deep-pressure play—may improve regulation, especially during transitions and physical care tasks.

In the Oral Sensory Processing domain, Sabrina scored in the “Just Like the Majority of Others” range. However, his caregiver noted some specific behaviors that may indicate early signs of oral sensitivity or defensiveness, including gagging on certain foods, holding food in his cheeks before swallowing, and a preference for one texture of food (e.g., smooth or crunchy). He also uses drinking to self-soothe, which may serve as a coping mechanism for sensory overload. While not yet significant, these oral behaviors could impact feeding variety and oral-motor skill development and may benefit from monitoring and structured oral exploration opportunities.

Overall, Sabrina’s sensory profile highlights a complex interplay of over-responsiveness, tactile defensiveness, sensory seeking, and under-responsiveness, particularly in the auditory, tactile, movement, and regulatory domains. These patterns affect his ability to engage in daily routines, transition between activities, and regulate his emotions. With proactive environmental supports, sensory-informed strategies, and collaborative caregiver coaching, Sabrina can be supported to increase independence, comfort, and successful participation across home and community settings.

RESPONSE FORMAT:
Return your response in the following JSON format only:
{"paragraphs": ["paragraph1", "paragraph2", ...]}

Where each paragraph is a complete section of your analysis (e.g., overall summary, general processing section, auditory processing section, etc.). Do not include any text before or after the JSON object.
"""




# Step 1: Upload the file
def upload_file(file_path):
    logger.info(f"Starting file upload: {file_path}")
    try:
        with open(file_path, "rb") as f:
            file = openai.files.create(file=f, purpose="assistants")
        logger.info(f"File uploaded successfully. File ID: {file.id}")
        return file.id
    except Exception as e:
        logger.error(f"Failed to upload file {file_path}: {str(e)}")
        raise

# Step 2: Create assistant (do this only once and reuse the ID)
def create_assistant():
    logger.info("Creating OpenAI assistant")
    try:
        assistant = openai.beta.assistants.create(
            name="PDF Assistant",
            instructions="You are a helpful assistant that answers questions about uploaded PDFs.",
            model="gpt-4-1106-preview",
            tools=[{"type": "file_search"}]
        )
        logger.info(f"Assistant created successfully. Assistant ID: {assistant.id}")
        return assistant.id
    except Exception as e:
        logger.error(f"Failed to create assistant: {str(e)}")
        raise

# Step 3: Create a thread
def create_thread():
    logger.info("Creating new thread")
    try:
        thread = openai.beta.threads.create()
        logger.info(f"Thread created successfully. Thread ID: {thread.id}")
        return thread.id
    except Exception as e:
        logger.error(f"Failed to create thread: {str(e)}")
        raise

# Step 4: Add user message to thread, with file attached via attachments
def add_message_to_thread(thread_id, prompt, file_ids):
    logger.info(f"Adding message to thread {thread_id} with {len(file_ids)} file(s)")
    try:
        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt,
            attachments=[{
                "file_id": file_id,
                "tools": [{"type": "file_search"}]
            } for file_id in file_ids]
        )
        logger.info(f"Message added to thread {thread_id} successfully")
    except Exception as e:
        logger.error(f"Failed to add message to thread {thread_id}: {str(e)}")
        raise

# Step 5: Run the assistant
def run_assistant(assistant_id, thread_id):
    logger.info(f"Starting assistant run. Assistant ID: {assistant_id}, Thread ID: {thread_id}")
    try:
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        logger.info(f"Assistant run started successfully. Run ID: {run.id}")
        return run.id
    except Exception as e:
        logger.error(f"Failed to start assistant run: {str(e)}")
        raise

# Step 6: Wait for the run to complete
def wait_for_run(thread_id, run_id):
    logger.info(f"Waiting for run {run_id} to complete")
    start_time = time.time()
    while True:
        try:
            run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.status == "completed":
                elapsed_time = time.time() - start_time
                logger.info(f"Run {run_id} completed successfully in {elapsed_time:.2f} seconds")
                return
            elif run.status in ["failed", "cancelled", "expired"]:
                logger.error(f"Run {run_id} failed with status: {run.status}")
                raise Exception(f"Run failed with status: {run.status}")
            
            # Log progress every 10 seconds
            if int(time.time() - start_time) % 10 == 0:
                logger.debug(f"Run {run_id} still in progress. Current status: {run.status}")
            
            time.sleep(1)
        except Exception as e:
            if "Run failed with status" in str(e):
                raise
            logger.error(f"Error while waiting for run {run_id}: {str(e)}")
            raise

# Step 7: Get the assistant's reply
def get_response(thread_id):
    logger.info(f"Retrieving response from thread {thread_id}")
    try:
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        for msg in messages.data:
            if msg.role == "assistant":
                logger.info(f"Assistant response retrieved successfully from thread {thread_id}")
                return msg.content[0].text.value
        
        logger.warning(f"No assistant response found in thread {thread_id}")
        return "No assistant response found."
    except Exception as e:
        logger.error(f"Failed to retrieve response from thread {thread_id}: {str(e)}")
        raise


def sensory_assistant(pdf_path: str):
    logger.info(f"Starting sensory profile analysis for file: {pdf_path}")
    try:
        file_path = pdf_path
        file_id = upload_file(file_path)
        assistant_id = create_assistant()
        thread_id = create_thread()
        add_message_to_thread(thread_id, PROMPT, [file_id])
        run_id = run_assistant(assistant_id, thread_id)
        wait_for_run(thread_id, run_id)
        response = get_response(thread_id)
        logger.info("Sensory profile analysis completed successfully")
        return response
    except Exception as e:
        logger.error(f"Sensory profile analysis failed: {str(e)}")
        raise

# Main execution
if __name__ == "__main__":
    logger.info("Starting main execution of sensory profile assistant")
    
    file_path = "/home/lap-49/Documents/ot-report/assets/inputs/Sensory-Profile-2-Summary-Report_70247631_1751134355067.pdf"
    
    try:
        file_id = upload_file(file_path)
        assistant_id = create_assistant()
        thread_id = create_thread()
        add_message_to_thread(thread_id, PROMPT, [file_id])
        run_id = run_assistant(assistant_id, thread_id)
        wait_for_run(thread_id, run_id)
        response = get_response(thread_id)
        print("Response:\n", response)
        logger.info("Main execution completed successfully")
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}")
        raise