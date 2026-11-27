// src/types/language.ts
/**
 * Types for language metadata returned by the backend.
 */
export interface LanguageInfo {
  id: number; // Judge0 language ID
  name: string; // e.g., "Python 3"
  monaco_id?: string; // monaco language identifier (e.g., "python")
  extension?: string; // e.g., ".py"
  aliases?: string[]; // optional aliases
}

export interface LanguagesResponse {
  languages: LanguageInfo[];
}
