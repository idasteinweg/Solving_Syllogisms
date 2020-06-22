import pygame, sys
from pygame.locals import *
import pygame_textinput
from math import sqrt
import random
from time import time
import csv
import os

SCREEN_SIZE = (800, 600)
MAX_PARTICIPANTS = 20
START_DELAY = 1.0  # s
BACKGROUND_COLOR = (255, 255, 255)


class Participant:
    def __init__(self, participant_id):
        """
        Participant class to handle all attributes of the participant and
        statistics about their performance.
        :param participant_id: unique participant ID
        """

        self.participant_id = participant_id

        # Current trial
        self.current_trial = 'Pre'

        # performance statistics
        self.false_positives = 0.0
        self.true_positives = 0.0
        self.true_negatives = 0.0
        self.false_negatives = 0.0
        self.responses = []
        self.mean_reaction_time = 0.0
        self.std_reaction_time = 0.0
        self.false_alarm_rate = 0.0
        self.hit_rate = 0.0

        # Strings to display performance
        self.summary_strings = []

    def compute_statistics(self, conclusions):
        """
        Update participant statistics after each trial.
        """

        # Get statistics from conclusions
        reaction_times = []
        
        for conclusion in conclusions.items:

             # Response of true
            if conclusion.user_input == True: #user_input = True if event.key == K_d else False
                self.responses.append(1)
                #true positives
                if conclusion.user_input == conclusion.label:
                    self.true_positives += 1
                    
                else: 
                    self.false_positives += 1
            # Response of false
            elif conclusion.user_input == False:
                self.responses.append(0)
                
                if conclusion.user_input == conclusion.label:
                     self.true_negatives += 1
                     
                else:
                    self.false_negatives += 1
                    

            # Append reaction time
            reaction_times.append(conclusion.reaction_time)
            
        #Compute hit and false alarm rate
        self.hit_rate = self.true_positives / (self.true_positives + self.false_negatives)
        self.false_alarm_rate = self.false_positives / (self.false_positives + self.true_negatives)

        # Compute reaction time statistics
        self.mean_reaction_time = round(sum(reaction_times) /
                                        len(reaction_times), 2)
        self.std_reaction_time = round(sqrt(sum((xi -
                                                 self.mean_reaction_time) ** 2
                                                for xi in reaction_times) /
                                            len(reaction_times)), 2)

        # Set summary strings
        summary_string_1 = 'You answered ' + str(self.true_positives + self.true_negatives) + ' of ' + \
                              str(len(conclusions.items)) + ' conclusions ' \
                                                            'correctly'
        summary_string_2 = 'with an average reaction time of ' \
                                + str(self.mean_reaction_time) + 's.'
        self.summary_strings = [summary_string_1, summary_string_2]

    def write_csv(self, conclusions):
        """
        Write participant's results to CSV file at the end of the experiment.
        """
        correctness = [1 if conclusion.label else 0 for conclusion in conclusions.items]
        with open("SolvingSyllogisms.csv", "a") as database:
            # Write results to csv file
            # Format: ID, number of attempts, mean, std
            writer = csv.writer(database)
            writer.writerow([self.participant_id, self.hit_rate, self.false_alarm_rate, self.true_positives, self.false_negatives, self.false_positives, self.true_negatives, self.mean_reaction_time, self.std_reaction_time, self.responses])


class Sequence:
    class Conclusion:
        def __init__(self, image, label):
            self.image = image
            self.label = label
            self.user_input = None
            self.reaction_time = None
            self.display_time = 0

    def __init__(self, sequence_type, image_folder_id):

        assert sequence_type in ['Premise', 'Conclusion', 'Test']
        self.type = sequence_type

        # Get root directory
        if self.type in ['Premise', 'Conclusion']:
            root = 'Images/' + image_folder_id + "/" + self.type + "s"
        else:
            root = 'Images/' + self.type

        # Set naming key to check for correct naming convention
        if self.type == 'Premise':
            naming_key = ['P']
        elif self.type == 'Conclusion':
            naming_key = ['F', 'T']
        else:
            naming_key = ['T']

        # Construct list of items
        self.items = self.load_images(root, naming_key)

        # Pointer to the currently displayed item
        self.item_pointer = 0

    def current_display_time(self):
        """
        Return display time of current item
        """

        return self.items[self.item_pointer].display_time

    def show(self, screen):

        current_item = self.items[self.item_pointer]
        if self.type in ['Premise', 'Test']:
            screen.blit(current_item, (0, 50))
        else:
            screen.blit(current_item.image, (0, 50))
            if self.current_display_time() == 0:
                self.items[self.item_pointer].display_time = time()

    def load_images(self, root, naming_key):
        """
        Load images from directory.
        """

        # Create container for all image objects
        items = []
        
        # Loop over all files in the root directory
        # os.listdir(root) returns a list of all file names in the directory
        for filename in sorted (os.listdir(root)):

            # Get complete path to image
            img_path = os.path.join(root, filename)

            # Check that file is of correct type and follows naming convention
            try:
                # filename has to start with P (Premise)
                # and file has to be a jpg-file
                key_digits = len(naming_key[0])
                assert filename[2:2+key_digits] in naming_key
            except AssertionError:
                print('Incorrect file type or naming convention detected in '
                      'filename' + str(img_path) + ". Skip file...")
                continue

            # If ConclusionSequence, create Conclusion object
            if self.type == 'Conclusion':

                # Load image
                image = pygame.image.load(img_path)

                # Construct label based on naming convention
                label = True if filename[2] == 'T' else False

                item = self.Conclusion(image, label)

            else:

                # Load image
                item = pygame.image.load(img_path)

            # Append object to list of objects
            
            items.append(item)

        return items


class Application:

    # Declare colors and fonts as static class variables
    BLACK, WHITE = (0, 0, 0), (255, 255, 255)
    BACKGROUND_COLOR = WHITE
    RED, GREEN, = (255, 0, 0), (0, 255, 0)
    BLUE, YELLOW = (0, 0, 255), (255, 255, 0)
    font = pygame.font.Font(None, 80)
    font_small = pygame.font.Font(None, 40)

    def __init__(self, screen_size, start_delay,
                 max_participants):
        """
    Constructor for application class. This class instantiates the GUI
    and handles all interaction with the participant.
    :param screen_size: tuple (int, int) | (width, height)
    :param box_parameters: dict | box parameters (number, size, dist., ...)
    :param start_delay: float | time before first corsi box is shown in s
    :param max_participants: int | maximum number of participants
    """

        # Initialize PyGame
        pygame.init()

        # Set screen size
        self.screen_size = screen_size
        pygame.display.set_mode((self.screen_size[0],
                                 self.screen_size[1]), 0, 32)

        # Set application title
        pygame.display.set_caption("Solving Syllogisms")

        # Get screen handle
        self.screen = pygame.display.get_surface()

        # Declare interface for text input
        self.text_input = pygame_textinput.TextInput()

        # Set initial state of the application
        self.state = 'Participant_ID'

        # Initialize participant ID to None (will be set in GUI)
        self.participant = None

        # Trial type (Pre or Post)
        # Will be inferred from CSV file after participant ID is known
        self.trial_type = None

        # List of premises (Sequence object with type premise)
        # Will be created after participant ID is known
        self.premises = None

        self.test = None

        # List of conclusion (Sequence object with type conclusion)
        # Will be created after participant ID is known
        self.conclusions = None
        
        # Last update time
        self.last_update = 0

        # Set trial parameters
        self.finished = False

        # Set maximum number of participants
        self.max_participants = max_participants

        # Set delay time between instruction
        self.start_delay = int(start_delay)

        # Load instruction image
        self.instruction_image = pygame.image.load(
            "InstructionImage.png")

    def start(self):

        # Loop until execution is terminated in GUI
        while True:
            # Create blank screen
            self.screen.fill(BACKGROUND_COLOR)

            # Handle events to set application state
            self.handle_events()

            # Update screen based on application state
            self.update_screen()

            # Refresh screen
            pygame.display.update()

    def handle_events(self):
        """
    Handle all available events.
    :param events: list of PyGame event objects
    """

        # Get list of events
        events = pygame.event.get()

        # Iterate over all events
        for event in events:

            # Pressing ESC or clicking X
            if event.type == QUIT or (event.type == KEYDOWN and
                                      event.key == K_ESCAPE):
                self.participant.write_csv(self.conclusions)
                pygame.quit()
                sys.exit()

            if self.state == 'Participant_ID':
                self.handle_id_input(event)

            elif self.state == 'Instructions':
                # Go to next state upon pressing of space bar and display
                # participant ID in GUI
                if event.type == KEYDOWN and event.key == K_SPACE:
                    pygame.display.set_caption("Solving Syllogisms "
                                               "Test: Participant " + str(
                        self.participant.participant_id))

                    # Show test in Pre trial
                    if self.trial_type == 'Pre':
                        self.state = 'Test'
                    else:
                        self.state = "Premise"

            elif self.state == 'Test':
                self.handle_test_input(event)

            elif self.state == "Premise":
                self.handle_premise_input(event)

            elif self.state == "Conclusion":
                self.handle_conclusion_input(event)

    def handle_id_input(self, event):

        # Update text input interface
        self.text_input.update([event])

        # Check if valid participant ID provided
        if event.type == KEYDOWN and event.key == K_RETURN:
            try:
                # Cast text input to integer
                participant_id = int(self.text_input.get_text())
            except ValueError:
                # Set participant_id to None if invalid input provided
                participant_id = None

            # Check that participant_id within range of allowed number of
            # participants
            if participant_id is not None and \
                    1 <= participant_id <= self.max_participants:
                # Create participant
                self.participant = Participant(participant_id)
                self.trial_type = self.get_trial_type(participant_id)
                
                # Get image folder determined by even or odd participant id
                if ((participant_id % 2) == 0 and self.trial_type == "Pre") or ((participant_id % 2) == 1 and self.trial_type == "Post"):
                    image_folder_id = "Folder1"
                else: 
                    image_folder_id = "Folder2"
                            
                self.premises = Sequence('Premise', image_folder_id)
                self.conclusions = Sequence('Conclusion', image_folder_id)
                if self.trial_type == 'Pre':
                    self.test = Sequence('Test', None)

                if self.trial_type == 'Pre':
                    # Set application state to "Instructions"
                    self.state = "Instructions"
                else:
                    # Set application state to "Instructions"
                    self.state = "Premise"

            else:
                print("Incorrect participant ID. Please type "
                      "a number between 1 and ", self.max_participants,
                      '!')

    def handle_test_input(self, event):
        test_id = self.test.item_pointer + 1
        
        if event.type == KEYDOWN and event.key == K_SPACE and not test_id in [5, 7] and \
                test_id < len(self.test.items):
            self.test.item_pointer += 1
        
        elif event.type == KEYDOWN and (event.key == K_d or event.key == K_k) and test_id in [5, 7] and \
                test_id < len(self.test.items):
            self.test.item_pointer += 1
            
        # Go to conclusions phase after last premise
        if test_id == len(self.test.items):
            if event.type == KEYDOWN and (event.key == K_SPACE):
                # Set state
                self.state = "Premise"

    def handle_premise_input(self, event):

        # Increment item pointer if not all premises have been displayed
        if event.type == KEYDOWN and event.key == K_SPACE and \
                self.premises.item_pointer < len(self.premises.items):
            self.premises.item_pointer += 1

        # Go to conclusions phase after last premise
        if self.premises.item_pointer == len(self.premises.items):
            if event.type == KEYDOWN and event.key == K_SPACE:

                # Set state
                self.state = "Conclusion"

    def handle_conclusion_input(self, event):
        """
        Handles events in state UserInput.
        :param event: PyGame event object
        """

        if event.type == KEYDOWN and (event.key == K_k or event.key == K_d):

            # Get user input
            user_input = True if event.key == K_d else False

            # Set user input attribute
            self.conclusions.items[
                self.conclusions.item_pointer].user_input = user_input

            # Get current time and compute reaction time
            end_time = time()
            reaction_time = end_time - self.conclusions.items[
                self.conclusions.item_pointer].display_time

            # Set reaction time attribute
            self.conclusions.items[
                self.conclusions.item_pointer].reaction_time = reaction_time

            # Increment item pointer
            self.conclusions.item_pointer += 1

            # End experiment with user input to last conclusion
            if self.conclusions.item_pointer == (len(self.conclusions.items)):

                # Set state
                self.state = 'End'

                # Compute performance statistics
                self.participant.compute_statistics(self.conclusions)

    def update_screen(self):
        """
        Update visual appearance based on current state of the application.
        """

        if self.state == 'Participant_ID':
            self.draw_id()

        elif self.state == 'Instructions':
            self.draw_instructions()

        elif self.state == 'Test':

            # Get premise ID
            test_id = self.test.item_pointer + 1

            # Show image
            self.test.show(self.screen)

            # Show instructions
            if test_id < 5:
                self.draw_text("Test Premise: " + str(test_id), self.font_small,
                           self.BLACK, BACKGROUND_COLOR, SCREEN_SIZE[1] * .1)
                self.draw_text("Press space bar to continue", self.font_small,
                           self.BLACK, BACKGROUND_COLOR, SCREEN_SIZE[1] * .8)
                
            elif test_id in [5, 7]:
                conclusion_id = 1 if test_id == 5 else 2
                self.draw_text("Test Conclusion: " + str(conclusion_id),
                               self.font_small,
                               self.BLACK, BACKGROUND_COLOR,
                               SCREEN_SIZE[1] * .1)
                self.draw_text("D: TRUE   K: FALSE", self.font,
                           self.BLACK, BACKGROUND_COLOR, SCREEN_SIZE[1] * .8)
            else:
                solution_id = 1 if test_id == 6 else 2
                self.draw_text("Test Solution: " + str(solution_id),
                               self.font_small,
                               self.BLACK, BACKGROUND_COLOR,
                               SCREEN_SIZE[1] * .1)
                self.draw_text("Press space bar to continue", self.font_small,
                           self.BLACK, BACKGROUND_COLOR, SCREEN_SIZE[1] * .8)
                
            if test_id == len(self.test.items):
                self.draw_text("Press space bar to start experiment",
                               self.font_small,
                               self.BLACK, BACKGROUND_COLOR,
                               SCREEN_SIZE[1] * .8)

        elif self.state == 'Premise':

            # Get premise ID
            premise_id = self.premises.item_pointer + 1

            # Show image
            self.premises.show(self.screen)

            # Show instructions
            self.draw_text("Premise: " + str(premise_id), self.font_small,
                           self.BLACK, BACKGROUND_COLOR, SCREEN_SIZE[1] * .1)
            self.draw_text("Press Spacebar to continue", self.font_small,
                           self.BLACK, BACKGROUND_COLOR, SCREEN_SIZE[1] * .8)

        elif self.state == 'Conclusion':

            # Get conclusion ID
            conclusion_id = self.conclusions.item_pointer + 1

            # Show image for 7 seconds
            last_display_time = self.conclusions.current_display_time()
            if (time() - last_display_time) < 7.0 or last_display_time == 0:
                self.conclusions.show(self.screen)

            # Show instructions
            self.draw_text("Conclusion: " + str(conclusion_id),
                           self.font_small, self.BLACK,
                           BACKGROUND_COLOR, SCREEN_SIZE[1] * .1)
            self.draw_text("D: TRUE   K: FALSE", self.font,
                           self.BLACK,
                           BACKGROUND_COLOR, SCREEN_SIZE[1] * .8)

        elif self.state == 'End':
            if self.trial_type == "Pre":
                self.draw_text("Thank you! You can close the window. ", self.font_small,
                           self.BLACK,
                           BACKGROUND_COLOR, SCREEN_SIZE[1] * .5)
            else:
                self.show_summary()
            


    def show_summary(self):
        # Display performance summary
        feedback1 = self.participant.summary_strings[0]
        self.draw_text(feedback1, self.font_small,
                       self.BLACK,
                       BACKGROUND_COLOR, SCREEN_SIZE[1] * .5)
        feedback2 = self.participant.summary_strings[1]
        self.draw_text(feedback2, self.font_small,
                       self.BLACK,
                       BACKGROUND_COLOR, SCREEN_SIZE[1] * .6)
        self.draw_text("End of Experiment", self.font,
                       self.BLACK,
                       BACKGROUND_COLOR, SCREEN_SIZE[1] * .2)

    def draw_id(self):
        self.draw_text("Solving Syllogisms", self.font, self.BLACK,
                       BACKGROUND_COLOR, 150)
        self.draw_text("Please enter your participant ID", self.font_small,
                       self.BLACK, BACKGROUND_COLOR, SCREEN_SIZE[1] * .8)
        self.screen.blit(self.text_input.get_surface(),
                         (SCREEN_SIZE[0] * .5, SCREEN_SIZE[1] * .5))

    def draw_instructions(self):
        self.screen.blit(self.instruction_image, (0, 0))

    def draw_text(self, text, font, color, bgcolor, ypos):
        text_surface = font.render(text, True, color, bgcolor)
        text_rectangle = text_surface.get_rect()
        text_rectangle.center = (SCREEN_SIZE[0] / 2.0, ypos)
        self.screen.blit(text_surface, text_rectangle)

    @staticmethod
    def get_trial_type(participant_id, filename='SolvingSyllogisms.csv'):
        # File doesn't yet exist
        if not os.path.isfile(filename):
            trial_type = 'Pre'

        else:
            trial_type = 'Pre'
            with open(filename) as f:
                reader = csv.reader(f)
                for row in reader:
                    id = int(row[0])
                    if id == participant_id:
                        trial_type = 'Post'

        return trial_type


if __name__ == '__main__':
    Application(SCREEN_SIZE, START_DELAY, MAX_PARTICIPANTS).start()
