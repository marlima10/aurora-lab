<?php
declare(strict_types=1);

namespace Aurora\Http\Requests;

use Aurora\Exceptions\ValidationException;
use DateTimeImmutable;

final class SaveFitnessStateRequest
{
    public static function validate(array $body, string $action): array
    {
        $people = $body['people'] ?? null;
        $entries = $body['entries'] ?? null;
        if (!is_array($people) || !is_array($entries) || count($people) > 500 || count($entries) > 50000) {
            throw new ValidationException('Formato de dados inválido');
        }
        foreach ($people as $person) {
            if (!is_array($person) || !isset($person['id'], $person['name']) || !is_string($person['id']) || !is_string($person['name'])) {
                throw new ValidationException('Cadastro de pessoa inválido');
            }
        }
        $activePersonDates = [];
        foreach ($entries as $entry) {
            if (!is_array($entry) || !isset($entry['id'], $entry['person']) || !is_string($entry['id']) || !is_string($entry['person'])) {
                throw new ValidationException('Registro de treino/peso inválido');
            }
            // Importação e merge preservam a compatibilidade com registros antigos.
            if ($action !== 'save') {
                continue;
            }
            $date = $entry['date'] ?? null;
            self::validateDate($date);
            if ($date !== null && $date !== '' && empty($entry['deletedAt'])) {
                $personDate = $entry['person'] . '|' . $date;
                if (isset($activePersonDates[$personDate])) {
                    throw new ValidationException('Já existe um registro ativo para essa pessoa e data');
                }
                $activePersonDates[$personDate] = true;
            }
            $weight = $entry['weight'] ?? null;
            if ($weight !== null && $weight !== '' && (!is_numeric($weight) || (float)$weight < 1 || (float)$weight > 500)) {
                throw new ValidationException('O peso deve estar entre 1 e 500 kg');
            }
        }
        return ['people' => $people, 'entries' => $entries];
    }

    private static function validateDate(mixed $date): void
    {
        if ($date === null || $date === '') {
            return;
        }
        if (!is_string($date) || !preg_match('/^\d{4}-\d{2}-\d{2}$/', $date)) {
            throw new ValidationException('Use uma data válida no formato AAAA-MM-DD');
        }
        $parsed = DateTimeImmutable::createFromFormat('!Y-m-d', $date);
        $errors = DateTimeImmutable::getLastErrors();
        if (!$parsed || ($errors !== false && ($errors['warning_count'] > 0 || $errors['error_count'] > 0)) || $parsed->format('Y-m-d') !== $date) {
            throw new ValidationException('A data informada não existe no calendário');
        }
        if ($date > date('Y-m-d')) {
            throw new ValidationException('Não é permitido salvar registros em datas futuras');
        }
    }
}
