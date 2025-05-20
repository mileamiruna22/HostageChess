// aiService.js
const API_BASE_URL = 'http://localhost:5000'; // Modificat portul la 5000 pentru Flask

const aiService = {
    startNewAIGame: async (playerColor, difficulty) => {
        try {
            const response = await fetch(`${API_BASE_URL}/new_ai_game`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ player_color: playerColor, difficulty: difficulty }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => {});
                throw new Error(errorData?.error || 'Eroare la începerea jocului nou cu AI');
            }

            return await response.json();
        } catch (error) {
            console.error('Eroare la startNewAIGame:', error);
            throw error;
        }
    },

    getAIMove: async (gameId, difficulty) => {
        try {
            const response = await fetch(`${API_BASE_URL}/ai_move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ game_id: gameId, difficulty: difficulty }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => {});
                throw new Error(errorData?.error || 'Eroare la obținerea mutării AI');
            }

            return await response.json();
        } catch (error) {
            console.error('Eroare la getAIMove:', error);
            throw error;
        }
    },

    aiExchangeHostage: async (gameId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/ai_exchange_hostage`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ game_id: gameId }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => {});
                throw new Error(errorData?.error || 'Eroare la schimbul de ostatici AI');
            }

            return await response.json();
        } catch (error) {
            console.error('Eroare la aiExchangeHostage:', error);
            throw error;
        }
    }
};

export default aiService;