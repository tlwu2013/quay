import React, {useState, useEffect} from 'react';
import {useBeforeUnload} from 'react-router-dom';
import {
  Alert,
  ActionGroup,
  Button,
  Form,
  FormGroup,
  TextInput,
  Checkbox,
  Select,
  SelectOption,
  NumberInput,
  Spinner,
} from '@patternfly/react-core';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {getOrganizationMirror, updateOrganizationMirror, syncNowOrganizationMirror, OrganizationMirror} from 'src/resources/OrganizationMirrorResource';
import {AlertVariant, useUI} from 'src/contexts/UIContext';
import {useFetchRobotAccounts} from 'src/hooks/useRobotAccounts';

interface OrganizationMirrorSettingsProps {
  organizationName: string;
}

export function OrganizationMirrorSettings({organizationName}: OrganizationMirrorSettingsProps) {
  const {addAlert} = useUI();
  const queryClient = useQueryClient();
  
  const {data: config, isLoading} = useQuery(['organizationMirror', organizationName], () =>
    getOrganizationMirror(organizationName).catch(e => {
        if (e.response?.status === 404 || e.response?.status === 401) return null;
        throw e;
    })
  );

  const {robots} = useFetchRobotAccounts(organizationName);

  const [formData, setFormData] = useState<Partial<OrganizationMirror>>({
    external_registry: '',
    external_namespace: '',
    external_registry_username: '',
    external_registry_password: '',
    sync_interval: 86400,
    repo_filter_type: 'regex',
    repo_filter_value: '',
    internal_robot: '',
    is_enabled: true,
  });
  
  const [isRobotSelectOpen, setIsRobotSelectOpen] = useState(false);
  const [isFilterTypeSelectOpen, setIsFilterTypeSelectOpen] = useState(false);

  // Track unsaved changes
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    if (config) {
      const loadedData = {
        ...config,
        external_registry_password: ''
      };
      setFormData(loadedData);
      setHasUnsavedChanges(false);
  } else if (!config) {
    // Load from sessionStorage if config failed to load
    const saved = sessionStorage.getItem(`mirror-config-${organizationName}`);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setFormData(prev => ({...prev, ...parsed}));
      } catch (e) {
        // Ignore invalid data
      }
    }
    // Ensure required fields are initialized for new organizations
    setFormData(prev => ({
      external_registry: prev.external_registry || '',
      external_namespace: prev.external_namespace || '',
      external_registry_username: prev.external_registry_username || '',
      external_registry_password: prev.external_registry_password || '',
      sync_interval: prev.sync_interval ?? 86400,
      repo_filter_type: prev.repo_filter_type || 'regex',
      repo_filter_value: prev.repo_filter_value || '',
      internal_robot: prev.internal_robot || '',
      is_enabled: prev.is_enabled ?? true,
      ...prev
    }));
  }
  }, [config, organizationName]);

  // Persist form data in sessionStorage
  useEffect(() => {
    const saved = sessionStorage.getItem(`mirror-config-${organizationName}`);
    if (saved && !config) {
      try {
        const parsed = JSON.parse(saved);
        setFormData(prev => ({...prev, ...parsed}));
      } catch (e) {
        // Ignore invalid data
      }
    }
  }, [organizationName, config]);

  // Track unsaved changes - set to true when form is modified after initial load
  const handleFormChange = (updater: (prev: Partial<OrganizationMirror>) => Partial<OrganizationMirror>) => {
    setFormData(updater);
    if (!hasUnsavedChanges) {
      setHasUnsavedChanges(true);
    }
  };

  // Warn before unloading with unsaved changes
  useBeforeUnload(
    React.useCallback(
      (event) => {
        if (hasUnsavedChanges) {
          event.preventDefault();
          return "You have unsaved changes. Are you sure you want to leave?";
        }
      },
      [hasUnsavedChanges]
    ),
    {capture: true}
  );

  useEffect(() => {
    if (formData.external_registry) {
      sessionStorage.setItem(`mirror-config-${organizationName}`, JSON.stringify({
        external_registry: formData.external_registry,
        external_namespace: formData.external_namespace,
        external_registry_username: formData.external_registry_username,
        sync_interval: formData.sync_interval,
        repo_filter_type: formData.repo_filter_type,
        repo_filter_value: formData.repo_filter_value,
        is_enabled: formData.is_enabled,
      }));
    }
  }, [formData, organizationName]);

  const updateMutation = useMutation((newConfig: Partial<OrganizationMirror>) =>
    updateOrganizationMirror(organizationName, newConfig), {
      onSuccess: (data) => {
        addAlert({variant: AlertVariant.Success, title: 'Mirror settings updated'});
        queryClient.invalidateQueries(['organizationMirror', organizationName]);
        // Reset unsaved changes after successful save
        setHasUnsavedChanges(false);
      },
      onError: (err: any) => {
         addAlert({variant: AlertVariant.Failure, title: 'Failed to update mirror settings', message: err.message});
      }
  });

  const syncNowMutation = useMutation(() =>
    syncNowOrganizationMirror(organizationName), {
      onSuccess: () => {
        addAlert({variant: AlertVariant.Success, title: 'Sync triggered successfully'});
        queryClient.invalidateQueries(['organizationMirror', organizationName]);
      },
      onError: (err: any) => {
         addAlert({variant: AlertVariant.Failure, title: 'Failed to trigger sync', message: err.message});
      }
  });

  const handleSubmit = () => {
    // Ensure all required fields are present
    const dataToSubmit = {
      external_registry: formData.external_registry || '',
      external_namespace: formData.external_namespace || '',
      external_registry_username: formData.external_registry_username || null,
      external_registry_password: formData.external_registry_password || null,
      sync_interval: formData.sync_interval ?? 86400,
      repo_filter_type: formData.repo_filter_type || 'regex',
      repo_filter_value: formData.repo_filter_value || null,
      internal_robot: formData.internal_robot || null,
      is_enabled: formData.is_enabled ?? true,
    };

    console.log('Form data being submitted:', dataToSubmit);
    updateMutation.mutate(dataToSubmit);
  };

  if (isLoading) return <Spinner />;
  
  return (
    <Form style={{maxWidth: '800px', padding: '20px'}}>
       {hasUnsavedChanges && (
         <Alert
           variant="warning"
           title="You have unsaved changes"
           style={{marginBottom: '20px'}}
         >
           Please save your changes before navigating away.
         </Alert>
       )}
       {config?.sync_status && (
           <Alert 
                variant={config.sync_status === 'success' ? 'success' : config.sync_status === 'failure' ? 'danger' : 'info'} 
                title={`Last Sync: ${config.sync_status}`}
                style={{marginBottom: '20px'}}
           >
               {config.sync_message}
               {config.last_sync_start && <div>Last Run: {new Date(config.last_sync_start).toLocaleString()}</div>}
           </Alert>
       )}
    
       <FormGroup label="Enable Mirroring" fieldId="is-enabled">
          <Checkbox
            id="is-enabled"
            label="Enable organization mirroring"
            isChecked={formData.is_enabled}
            onChange={(_e, val) => handleFormChange(prev => ({...prev, is_enabled: val}))}
          />
       </FormGroup>

       <FormGroup label="External Registry URL" fieldId="external-registry" isRequired helperText="e.g. https://harbor.example.com">
          <TextInput 
            id="external-registry" 
            value={formData.external_registry} 
            onChange={(_event, val) => handleFormChange(prev => ({...prev, external_registry: val}))}
          />
       </FormGroup>

       <FormGroup label="External Namespace/Project" fieldId="external-namespace" isRequired>
          <TextInput
            id="external-namespace"
            value={formData.external_namespace}
            onChange={(_event, val) => handleFormChange(prev => ({...prev, external_namespace: val}))}
          />
       </FormGroup>

       <FormGroup label="Registry Username" fieldId="reg-username">
          <TextInput
            id="reg-username"
            value={formData.external_registry_username || ''}
            onChange={(_event, val) => handleFormChange(prev => ({...prev, external_registry_username: val}))}
          />
       </FormGroup>

       <FormGroup label="Registry Password" fieldId="reg-password">
          <TextInput
            id="reg-password"
            type="password"
            value={formData.external_registry_password || ''}
            onChange={(_event, val) => handleFormChange(prev => ({...prev, external_registry_password: val}))} 
          />
       </FormGroup>

       <FormGroup label="Sync Interval (seconds)" fieldId="sync-interval">
          <NumberInput 
            id="sync-interval" 
            value={formData.sync_interval} 
            onMinus={() => handleFormChange(prev => ({...prev, sync_interval: (prev.sync_interval || 0) - 3600}))}
            onPlus={() => handleFormChange(prev => ({...prev, sync_interval: (prev.sync_interval || 0) + 3600}))}
            onChange={(event) => handleFormChange(prev => ({...prev, sync_interval: Number((event.target as HTMLInputElement).value)}))}
          />
       </FormGroup>
       
       <FormGroup label="Repository Filter Type" fieldId="filter-type">
         <select
            className="pf-v5-c-form-control"
            id="filter-type"
            value={formData.repo_filter_type}
            onChange={(e) => {
                handleFormChange(prev => ({...prev, repo_filter_type: e.target.value as 'regex' | 'list'}));
            }}
         >
            <option value="regex">Regular Expression</option>
            <option value="list">Comma-separated List</option>
         </select>
       </FormGroup>
       
       <FormGroup label="Filter Value" fieldId="filter-value">
          <TextInput 
            id="filter-value" 
            value={formData.repo_filter_value || ''} 
            onChange={(_event, val) => handleFormChange(prev => ({...prev, repo_filter_value: val}))}
          />
       </FormGroup>

       <FormGroup label="Robot Account" fieldId="internal-robot" isRequired helperText="Robot account to use for creating repositories">
          <select
             className="pf-v5-c-form-control"
             id="internal-robot"
             value={formData.internal_robot || ''}
             onChange={(e) => {
                 handleFormChange(prev => ({...prev, internal_robot: e.target.value}));
             }}
          >
             <option value="" disabled>Select a robot account</option>
             {(robots || []).map(robot => (
                 <option key={robot.name} value={robot.name}>{robot.name}</option>
             ))}
          </select>
       </FormGroup>

       <ActionGroup>
         <Button variant="primary" onClick={handleSubmit} isLoading={updateMutation.isLoading}>Save Configuration</Button>
         <Button
           variant="secondary"
           onClick={() => syncNowMutation.mutate()}
           isLoading={syncNowMutation.isLoading}
           isDisabled={!config}
         >
           Sync Now
         </Button>
       </ActionGroup>
    </Form>
  );
}
