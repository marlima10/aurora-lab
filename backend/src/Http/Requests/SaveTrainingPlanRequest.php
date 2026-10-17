<?php
declare(strict_types=1);

namespace Aurora\Http\Requests;

use Aurora\Exceptions\ValidationException;

final class SaveTrainingPlanRequest
{
    public static function validate(array $body): array
    {
        $personId = $body['personId'] ?? null;
        $plans = $body['plans'] ?? null;
        $schedule = $body['schedule'] ?? null;
        if (!is_string($personId) || $personId === '' || !is_array($plans) || count($plans) !== 4
            || !is_array($schedule) || count($schedule) > 7) {
            throw new ValidationException('Plano ou agenda em formato inválido');
        }
        $byCode = [];
        foreach ($plans as $plan) {
            self::validatePlan($plan);
            if (isset($byCode[$plan['code']])) {
                throw new ValidationException('Ficha de treino inválida');
            }
            foreach ($plan['exercises'] as $exercise) {
                self::validateExercise($exercise);
            }
            $byCode[$plan['code']] = $plan;
        }
        $days = [];
        foreach ($schedule as $slot) {
            if (!is_array($slot) || !isset($slot['weekday'], $slot['planCode']) || !is_numeric($slot['weekday'])
                || !is_string($slot['planCode']) || (int)$slot['weekday'] < 0 || (int)$slot['weekday'] > 6
                || !isset($byCode[$slot['planCode']]) || isset($days[(int)$slot['weekday']])) {
                throw new ValidationException('Agenda semanal inválida');
            }
            $time = $slot['time'] ?? null;
            if ($time !== null && $time !== '' && (!is_string($time) || !preg_match('/^(?:[01]\d|2[0-3]):[0-5]\d$/', $time))) {
                throw new ValidationException('Horário inválido');
            }
            $days[(int)$slot['weekday']] = $slot;
        }
        return [
            'personId' => $personId, 'plans' => $byCode, 'days' => $days,
            'expectedRevision' => isset($body['expectedRevision']) ? (int)$body['expectedRevision'] : -1,
        ];
    }

    private static function validatePlan(mixed $plan): void
    {
        if (!is_array($plan) || !isset($plan['id'], $plan['code'], $plan['name'], $plan['exercises'])
            || !is_string($plan['id']) || !is_string($plan['code']) || !is_string($plan['name'])
            || !is_array($plan['exercises']) || !in_array($plan['code'], ['A', 'B', 'C', 'D'], true)
            || count($plan['exercises']) > 40) {
            throw new ValidationException('Ficha de treino inválida');
        }
    }

    private static function validateExercise(mixed $exercise): void
    {
        if (!is_array($exercise) || !isset($exercise['id'], $exercise['catalogId'], $exercise['muscleGroup'], $exercise['name'], $exercise['mode'])
            || !is_string($exercise['id']) || !is_string($exercise['catalogId']) || !is_string($exercise['muscleGroup'])
            || !is_string($exercise['name']) || !in_array($exercise['mode'], ['strength', 'cardio'], true)) {
            throw new ValidationException('Exercício inválido');
        }
        if ($exercise['mode'] === 'strength' && (!isset($exercise['sets'], $exercise['reps'])
            || (int)$exercise['sets'] < 1 || (int)$exercise['sets'] > 20 || (int)$exercise['reps'] < 1 || (int)$exercise['reps'] > 100)) {
            throw new ValidationException('Informe séries e repetições válidas');
        }
        if ($exercise['mode'] === 'cardio' && (!isset($exercise['durationMinutes'])
            || (int)$exercise['durationMinutes'] < 1 || (int)$exercise['durationMinutes'] > 1440)) {
            throw new ValidationException('Informe o tempo de cardio em minutos');
        }
    }
}
