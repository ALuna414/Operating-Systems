// imports needed for code to run
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

#define NUM_CARDS 52 // total cards in a deck
#define NUM_PLAYERS 6 // total player
#define NUM_ROUNDS 6  // total rounds

pthread_mutex_t gameMutex;
pthread_cond_t turnCondition;

int deck[NUM_CARDS];
int deckIndex = 0;
int targetCard = 0;
bool isRoundOver = false;
int currentRound = 0;

// Player Account Struc
typedef struct
{
    int playerNum;
    int hand[2];
    bool roundVictory;
} player_account;

player_account player_accounts[NUM_PLAYERS];

FILE *gameLogFile;

// Function declarations
void initDeck();
void shuffleDeck();
void *playerPlay(void *arg);
void *dealerDeal(void *arg);
void handleDealerTurn(int currentPlayerNum);
void handlePlayerTurn(player_account *playerAccount, int currentRound);
void printDeck(int deck[], int size);
void shiftDeckLeftAndAddDiscard(int discardedCard);

// FUNCTION DEFINITIONS

// PLAYER THREAD FUNCTION
// 
void *playerPlay(void *arg)
{
    // Cast argument to player account
    player_account *player = (player_account *)arg;

    int playerNumber = player->playerNum;

    pthread_mutex_lock(&gameMutex);

    // Draw a card for the player
    player->hand[1] = deck[deckIndex++];

    fprintf(gameLogFile, "\nPlayer %d draws a %d\n", playerNumber + 1, player->hand[1]);
    fprintf(gameLogFile, "Player %d Hand: <%d, %d>\n", playerNumber + 1, player->hand[0], player->hand[1]);
    printf("Player %d Hand: <%d, %d>\n", playerNumber + 1, player->hand[0], player->hand[1]);

    // Check if player has won the round
    if (player->hand[0] == targetCard || player->hand[1] == targetCard)
    {
        player->roundVictory = true;
        printf("Player %d wins round %d with matching card %d\n\n", playerNumber + 1, currentRound + 1, targetCard);
        fprintf(gameLogFile, "Player %d wins round %d with matching card %d\n\n", playerNumber + 1, currentRound + 1, targetCard);
        isRoundOver = true;
    }
    else
    {
        // Player loses the round
        printf("Player %d loses round %d\n", playerNumber + 1, currentRound + 1);

        // Discard a random card
        int discardIndex = rand() % 2;
        fprintf(gameLogFile, "Player %d discards card: %d\n", playerNumber + 1, player->hand[discardIndex]);

        // Shift deck and add discarded card
        shiftDeckLeftAndAddDiscard(player->hand[discardIndex]);

        // Update player's hand
        int remainingCardIndex = (discardIndex == 0) ? 1 : 0;
        fprintf(gameLogFile, "Player %d Hand: <%d>\n", playerNumber + 1, player->hand[remainingCardIndex]);

        // Log deck
        printDeck(deck, NUM_CARDS);
    }

    pthread_mutex_unlock(&gameMutex);

    return NULL;
}

// DEALER THREAD FUNCTION
// 
void *dealerDeal(void *arg)
{
    // Cast argument to player account
    player_account *player = (player_account *)arg;

    int currentPlayerNum = player->playerNum;

    pthread_mutex_lock(&gameMutex);

    // Reset round status
    isRoundOver = false;

    // Shuffle deck and draw target card
    shuffleDeck();

    targetCard = deck[deckIndex++];

    fprintf(gameLogFile, "--------------------------------------------------------\n");
    fprintf(gameLogFile, "ROUND%d\n", currentRound + 1);
    fprintf(gameLogFile, "--------------------------------------------------------\n");
    fprintf(gameLogFile, "DEALER %d DRAWS TARGET CARD: %d\n", currentPlayerNum + 1, targetCard);
    printf("---------------------ROUND%d-------------------------------\n", currentRound + 1);
    printf("DEALER %d DRAWS TARGET CARD: %d\n", currentPlayerNum + 1, targetCard);

    // Deal cards to players
    for (int i = 0; i < NUM_PLAYERS; i++)
    {
        int playerIndex = (currentPlayerNum + i + 1) % NUM_PLAYERS;
        player_accounts[playerIndex].hand[0] = deck[deckIndex++];
        fprintf(gameLogFile, "DEALER %d DEALS a %d TO PLAYER%d\n", currentPlayerNum + 1, player_accounts[playerIndex].hand[0], playerIndex + 1);
        printf("DEALER %d DEALS a %d TO PLAYER%d\n", currentPlayerNum + 1, player_accounts[playerIndex].hand[0], playerIndex + 1);
    }

    pthread_mutex_unlock(&gameMutex);

    return NULL;
}

// SHIFT DECK LEFT AND ADD DISCARDED CARD
//
void shiftDeckLeftAndAddDiscard(int discardedCard)
{
    for (int i = 1; i < NUM_CARDS; ++i)
    {
        deck[i - 1] = deck[i];
    }
    deck[NUM_CARDS - 1] = discardedCard;

    deckIndex--;
}

// PRINT DECK
// 
void printDeck(int deck[], int size)
{
    printf("Deck: ");
    for (int i = deckIndex; i < size; ++i)
    {
        printf("%d ", deck[i]);
        fprintf(gameLogFile, "%d ", deck[i]);
    }
    fprintf(gameLogFile, "\n");
    printf("\n");
}

// EMPTY PLAYER TURN HANDLER
//
void handlePlayerTurn(player_account *player, int roundNum)
{
}

// EMPTY DEALER TURN HANDLER
// 
void handleDealerTurn(int currentPlayerNum)
{
}

// INITIALIZE DECK
//
void initDeck()
{
    for (int i = 0; i < NUM_CARDS; i++)
    {
        deck[i] = i % 13 + 1;
    }
    shuffleDeck();
}

// SHUFFLE DECK
//
void shuffleDeck()
{
    for (int i = 0; i < NUM_CARDS; i++)
    {
        int j = rand() % (i + 1);
        int temp = deck[i];
        deck[i] = deck[j];
        deck[j] = temp;
    }
    deckIndex = 0;
}

// MAIN CODE 
//
int main(int argc, char *argv[])
{
    // Initialize random seed
    int randomSeed = argc > 1 ? atoi(argv[1]) : time(NULL);
    srand(randomSeed);
    printf("Random Seed: %d\n", randomSeed);

    pthread_t playerThreads[NUM_PLAYERS];

    // Open game log file
    gameLogFile = fopen("game_log.txt", "w");
    if (gameLogFile == NULL)
    {
        perror("Error opening log file");
        exit(1);
    }

    // Initialize deck and mutex
    initDeck();
    pthread_mutex_init(&gameMutex, NULL);
    pthread_cond_init(&turnCondition, NULL);

    // Initialize player accounts
    for (int i = 0; i < NUM_PLAYERS; i++)
    {
        player_accounts[i].playerNum = i;
    }

    // Define the dealer index
    int dealerIndex = 0;

    // Start rounds
    for (int roundIndex = 0; roundIndex < NUM_ROUNDS; roundIndex++)
    {
        currentRound = roundIndex;

        dealerIndex = roundIndex % NUM_PLAYERS;

        // Dealer deals cards
        pthread_create(&playerThreads[dealerIndex], NULL, dealerDeal, (void *)&player_accounts[dealerIndex]);
        pthread_join(playerThreads[dealerIndex], NULL);

        // Iterate through players starting from the player after the dealer
        bool roundWinnerFound = false;
        for (int i = 1; i <= NUM_PLAYERS; i++)
        {
            int playerIndex = (dealerIndex + i) % NUM_PLAYERS;

            // Players play their turns
            pthread_create(&playerThreads[playerIndex], NULL, playerPlay, (void *)&player_accounts[playerIndex]);
            pthread_join(playerThreads[playerIndex], NULL);

            // Check if a player has won the round
            if (player_accounts[playerIndex].roundVictory)
            {
                roundWinnerFound = true;
                break;
            }
        }

        // Skip to the next round if a winner is found
        if (roundWinnerFound)
        {
            for (int i = 0; i < NUM_PLAYERS; i++)
            {
                if (!player_accounts[i].roundVictory)
                {
                    fprintf(gameLogFile, "Player %d lost round %d\n", i + 1, roundIndex + 1);
                }
                player_accounts[i].roundVictory = false;
            }
            continue; // Skip to the next round
        }

        // Log players who lost the round
        for (int i = 0; i < NUM_PLAYERS; i++)
        {
            if (!player_accounts[i].roundVictory)
            {
                fprintf(gameLogFile, "Player %d lost round %d\n", i + 1, roundIndex + 1);
            }
            player_accounts[i].roundVictory = false;
        }
    }

    // Close game log file and clean up resources
    fclose(gameLogFile);
    pthread_mutex_destroy(&gameMutex);
    pthread_cond_destroy(&turnCondition);

    return 0;
}
