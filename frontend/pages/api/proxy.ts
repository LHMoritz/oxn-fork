import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    const { method, body } = req;

    try {
        const response = await fetch('https://dein-backend-endpunkt/api', {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: method === 'GET' ? undefined : JSON.stringify(body),
        });

        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        console.error('Error in proxy handler:', error);
        res.status(500).json({ message: 'Internal Server Error' });
    }
}
