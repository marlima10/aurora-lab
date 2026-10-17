<?php
declare(strict_types=1);

namespace Aurora\Http\Requests;

use Aurora\Exceptions\ValidationException;

final class SaveExerciseRequest
{
    public static function validate(array $body): array
    {
        $exercise = $body['exercise'] ?? null;
        if (!is_array($exercise)) {
            throw new ValidationException('Cadastro de exercício inválido');
        }
        foreach (['id', 'muscleGroup', 'name', 'mode'] as $field) {
            if (!isset($exercise[$field]) || !is_string($exercise[$field])) {
                throw new ValidationException('Cadastro de exercício inválido');
            }
        }
        if (!in_array($exercise['mode'], ['strength', 'cardio'], true)) {
            throw new ValidationException('Cadastro de exercício inválido');
        }
        $id = trim($exercise['id']);
        $muscle = trim($exercise['muscleGroup']);
        $name = trim($exercise['name']);
        if ($id === '' || $muscle === '' || $name === '' || strlen($id) > 100 || strlen($muscle) > 80 || strlen($name) > 140) {
            throw new ValidationException('Preencha músculo/grupo e nome do exercício');
        }
        $youtube = $exercise['youtubeUrl'] ?? '';
        if (!is_string($youtube)) {
            throw new ValidationException('Use um link HTTPS válido do YouTube');
        }
        $youtube = trim($youtube);
        self::validateYoutube($youtube);
        return ['id' => $id, 'muscleGroup' => $muscle, 'name' => $name, 'mode' => $exercise['mode'], 'youtubeUrl' => $youtube];
    }

    private static function validateYoutube(string $url): void
    {
        if ($url === '') {
            return;
        }
        $parts = parse_url($url);
        $hosts = ['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be', 'www.youtu.be', 'youtube-nocookie.com', 'www.youtube-nocookie.com'];
        $host = strtolower((string)($parts['host'] ?? ''));
        if (($parts['scheme'] ?? '') !== 'https' || !in_array($host, $hosts, true) || strlen($url) > 500) {
            throw new ValidationException('Use um link HTTPS válido do YouTube');
        }
    }
}
