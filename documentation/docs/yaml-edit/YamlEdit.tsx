import React from "react";
import Form from "@rjsf/core";
import YAML from "yaml";
import validator from "@rjsf/validator-ajv8";
import { getDefaultFormState, type CustomValidator, type RJSFSchema, type UiSchema } from "@rjsf/utils";

import { sim2seisSchema } from "./schema";
import {
  CheckboxOptionalDataControlsTemplate,
  KeyLabelWrapIfAdditionalTemplate,
  LabelledAddButton,
  LabelledMoveDownButton,
  LabelledMoveUpButton,
  LabelledRemoveButton,
  NoDuplicateLabelFieldTemplate,
  TextNumberBaseInputTemplate,
} from "./rjsf-extras";
import "./yaml-edit.css";

import {
  Button,
  Icon,
  Dialog,
  TextField,
  Snackbar,
} from "@equinor/eds-core-react";

import { copy } from "@equinor/eds-icons";

import { TranslatableString, englishStringTranslator, replaceStringParameters } from '@rjsf/utils';

function customStrings(stringToTranslate: TranslatableString, params?: string[]): string {
  if(stringToTranslate === TranslatableString.KeyLabel) {
    return replaceStringParameters('Key:', params);
  }
  if(stringToTranslate === TranslatableString.OptionalObjectAdd || stringToTranslate === TranslatableString.OptionalObjectRemove) {
    return 'Include';
  }

  return englishStringTranslator(stringToTranslate, params);
}

function getGlobalAttributes(formData: unknown): string[] {
  if (typeof formData !== "object" || formData === null) {
    return [];
  }
  const globalConfig = (formData as { global?: unknown }).global;
  if (typeof globalConfig !== "object" || globalConfig === null) {
    return [];
  }
  const attributes = (globalConfig as { attributes?: unknown }).attributes;
  return Array.isArray(attributes)
    ? attributes.filter((attribute): attribute is string => typeof attribute === "string")
    : [];
}


function removeUndefinedValues(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(removeUndefinedValues);
  }
  if (typeof value !== "object" || value === null) {
    return value;
  }
  return Object.fromEntries(
    Object.entries(value)
      .filter(([, child]) => child !== undefined)
      .map(([key, child]) => [key, removeUndefinedValues(child)]),
  );
}

type YamlEditProps = {
  schema?: RJSFSchema;
  uiSchema?: UiSchema;
  customValidate?: CustomValidator;
  // Separate sessionStorage key per form so two pages do not share saved input
  storageKey?: string;
};

export const YamlEdit = ({ schema = sim2seisSchema, uiSchema = {}, customValidate, storageKey = "formData" }: YamlEditProps) => {
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const [snackbarOpen, setSnackbarOpen] = React.useState(false);
  const [formInstance, setFormInstance] = React.useState(0);

  const [initialConfig, setInitialConfig] = React.useState(() => {
    const savedFormData = sessionStorage.getItem(storageKey);
    if (savedFormData) {
      try {
        return JSON.parse(savedFormData);
      } catch (error) {
        console.error('Failed to parse saved form data:', error);
        return {};
      }
    }
    return {};
  });

  const [globalAttributes, setGlobalAttributes] = React.useState(() => getGlobalAttributes(initialConfig));
  const userInputRef = React.useRef(initialConfig);

  // RJSF does not emit onChange when (re)mounted with data, so validate replaced data here
  const isValid = (data: unknown) =>
    validator.validateFormData(data, schema, customValidate).errors.length === 0;
  const [validInput, setValidInput] = React.useState(() => isValid(initialConfig));

  const populateDefaults = () => {
    const currentFormData = removeUndefinedValues(userInputRef.current);
    const populatedFormData = getDefaultFormState(
      validator,
      schema,
      currentFormData,
      schema,
      false,
      { emptyObjectFields: "populateAllDefaults" },
    );
    if (typeof populatedFormData !== "object" || populatedFormData === null || Array.isArray(populatedFormData)) {
      return;
    }
    userInputRef.current = populatedFormData;
    setInitialConfig(populatedFormData);
    setGlobalAttributes(getGlobalAttributes(populatedFormData));
    setValidInput(isValid(populatedFormData));
    sessionStorage.setItem(storageKey, JSON.stringify(populatedFormData));
  };

  React.useEffect(() => {
    // Clear session storage when the user reloads same tab
    const handleBeforeUnload = () => {
      sessionStorage.removeItem(storageKey);
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [storageKey]);

  const yamlOutput =
    (validInput ? "" : "# This YAML file is not complete/valid\n\n") +
    YAML.stringify(userInputRef.current);

  return (
    <div>
      <div className="flex w-full justify-center my-10 gap-10">
        <button
          className="flex gap-2 font-bold items-center shadow p-1 rounded-lg bg-gray-100 hover:bg-gray-50 dark:bg-gray-800"
          onClick={() => {
            const input = document.createElement("input");
            input.type = "file";
            input.accept=".yml,.yaml"

            input.onchange = (e) => {
              if(e.target == null || !(e.target instanceof HTMLInputElement) || e.target.files == null){
                return
              }
              const file = e.target.files[0];
              const reader = new FileReader();
              reader.readAsText(file);

              reader.onload = (readerEvent) => {
                if(readerEvent.target == null){
                  console.error("No data target")
                  return
                }
                const content = readerEvent.target.result as string;
                const loadedConfig = YAML.parse(content);
                userInputRef.current = loadedConfig;
                sessionStorage.setItem(storageKey, JSON.stringify(loadedConfig));
                setGlobalAttributes(getGlobalAttributes(loadedConfig));
                setValidInput(isValid(loadedConfig));
                setInitialConfig(loadedConfig);
                setFormInstance((instance) => instance + 1);
              };
            };
            input.click();
          }}
        >
          Load config (YAML)
        </button>
        <button
          className="flex gap-2 font-bold items-center shadow p-1 rounded-lg bg-gray-100 hover:bg-gray-50" onClick={() => setDialogOpen(true)}>
          Config output (YAML)
        </button>
        <Dialog
          open={dialogOpen}
          onClose={() => {
            setDialogOpen(false);
            setSnackbarOpen(false);
          }}
          isDismissable={true}
          style={{ width: "min(90vw, 900px)" }}
        >
          <Dialog.Header>
            <Dialog.Title>YAML output</Dialog.Title>
          </Dialog.Header>
          <Dialog.CustomContent>
            <TextField
              id="yaml-content"
              style={{ width: "100%" }}
              multiline={true}
              placeholder={yamlOutput}
              rowsMax={50}
              readOnly={true}
            />
            <Button
              type="button"
              onClick={() => {
                navigator.clipboard.writeText(yamlOutput);
                setSnackbarOpen(true);
              }}
              className="mt-4"
            >
              <Icon data={copy} size={16}></Icon>
              Copy to clipboard
            </Button>
            <Snackbar
              open={snackbarOpen}
              onClose={() => setSnackbarOpen(false)}
            >
              YAML configuration file copied to clipboard
            </Snackbar>
          </Dialog.CustomContent>
        </Dialog>
        <button
          type="button"
          className="flex gap-2 font-bold items-center shadow p-1 rounded-lg bg-gray-100 hover:bg-gray-50 dark:bg-gray-800"
          onClick={populateDefaults}
        >
          Populate defaults
        </button>

      </div>
      <div className="flex justify-center my-20">
        <div className="p-10 shadow-lg rounded bg-slate-50 border-2 border-slate-50" style={{minWidth: 800}}>
          <Form
            key={formInstance}
            schema={schema}
            validator={validator}
            customValidate={customValidate}
            formData={initialConfig}
            formContext={{ globalAttributes }}
            experimental_defaultFormStateBehavior={{
              emptyObjectFields: "skipDefaults",
            }}
            onChange={(event) => {
              userInputRef.current = event.formData;
              setInitialConfig(event.formData);
              setGlobalAttributes(getGlobalAttributes(event.formData));
              sessionStorage.setItem(storageKey, JSON.stringify(event.formData));
              setValidInput(event.errors.length === 0);
            }}
            liveValidate
            uiSchema={{
              ...uiSchema,
              "ui:submitButtonOptions": { norender: true },
              "ui:globalOptions": {
                enableMarkdownInDescription: true,
              },
            }}
            templates={{
              FieldTemplate: NoDuplicateLabelFieldTemplate,
              BaseInputTemplate: TextNumberBaseInputTemplate,
              WrapIfAdditionalTemplate: KeyLabelWrapIfAdditionalTemplate,
              OptionalDataControlsTemplate: CheckboxOptionalDataControlsTemplate,
              ButtonTemplates: {
                AddButton: LabelledAddButton,
                RemoveButton: LabelledRemoveButton,
                MoveUpButton: LabelledMoveUpButton,
                MoveDownButton: LabelledMoveDownButton,
              },
            }}
            showErrorList={false}
            translateString={customStrings}
          />
        </div>
      </div>
    </div>
  );
}
