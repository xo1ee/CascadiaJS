export const labelClassName =
  "mb-1.5 block text-sm font-medium text-zinc-700 dark:text-zinc-300";

export const inputClassName =
  "w-full rounded-lg border border-zinc-200 bg-white px-3.5 py-2.5 text-sm text-zinc-900 shadow-sm outline-none transition placeholder:text-zinc-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-emerald-400 dark:focus:ring-emerald-400/20";

export function FormField({
    id,
    label,
    name,
    value,
    onChange,
    placeholder,
    hint,
  }: {
    id: string;
    label: string;
    name: string;
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    placeholder: string;
    hint?: string;
  }) {
    return (
      <div>
        <label htmlFor={id} className={labelClassName}>
          {label}
        </label>
        <input
          type="text"
          id={id}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={inputClassName}
        />
        {hint ? (
          <p className="mt-1.5 text-xs text-zinc-500 dark:text-zinc-400">{hint}</p>
        ) : null}
      </div>
    );
  }