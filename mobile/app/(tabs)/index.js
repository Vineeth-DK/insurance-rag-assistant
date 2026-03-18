import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, Alert, ActivityIndicator } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';

export default function App() {
  // State variables to hold user input and app status
  const [apiKey, setApiKey] = useState('');
  const [clientName, setClientName] = useState('');
  const [clientAge, setClientAge] = useState('');
  const [claimFactors, setClaimFactors] = useState('');
  const [pdfFiles, setPdfFiles] = useState([]); // Array to hold multiple files
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  // Your IP address
  const BACKEND_URL = 'ENTER YOU IP ADDRESS';

  // Function to pick multiple PDFs from the phone
  const pickDocument = async () => {
    let result = await DocumentPicker.getDocumentAsync({ 
      type: 'application/pdf',
      multiple: true 
    });
    if (!result.canceled) {
      setPdfFiles(result.assets); // Store the array of selected files
    }
  };

  // Function to send the PDFs to the backend
  const uploadAndAnalyze = async () => {
    // 1. Updated validation to check if the pdfFiles array is empty
    if (pdfFiles.length === 0 || !apiKey || !clientName || !clientAge || !claimFactors) {
      Alert.alert("Missing Info", "Please fill out all fields and select at least one PDF.");
      return;
    }

    setLoading(true);
    setAnswer('');

    try {
      // Step 1: Upload the PDFs
      const formData = new FormData();
      
      // 2. Loop through the array and append each file under the key 'files' (plural)
      pdfFiles.forEach((file) => {
        formData.append('files', {
          uri: file.uri,
          name: file.name,
          type: file.mimeType || 'application/pdf',
        });
      });

      const uploadRes = await fetch(`${BACKEND_URL}/upload`, {
        method: 'POST',
        body: formData,
        // 3. Removed the 'Content-Type' header here so the browser can set the boundary automatically!
      });
      
      if (!uploadRes.ok) throw new Error("Failed to upload documents.");

      // Step 2: Ask the question
      const analyzeRes = await fetch(`${BACKEND_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_name: clientName,
          client_age: parseInt(clientAge),
          claim_factors: claimFactors,
          api_key: apiKey
        }),
      });

      const analyzeData = await analyzeRes.json();
      
      if (analyzeData.success) {
        setAnswer(analyzeData.answer);
      } else {
        throw new Error("Failed to analyze.");
      }

    } catch (error) {
      Alert.alert("Error", error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.header}>Insurance RAG Assistant</Text>

      <TextInput
        style={styles.input}
        placeholder="Enter LLM API Key"
        value={apiKey}
        onChangeText={setApiKey}
        secureTextEntry
      />

      <TouchableOpacity style={styles.button} onPress={pickDocument}>
        {/* 4. Updated button text to show the number of files selected */}
        <Text style={styles.buttonText}>
          {pdfFiles.length > 0 ? `Selected: ${pdfFiles.length} File(s)` : "1. Select Policy PDF(s)"}
        </Text>
      </TouchableOpacity>

      {/* 5. NEW UI: Display a list of the names of the selected PDFs */}
      {pdfFiles.length > 0 && (
        <View style={styles.fileListContainer}>
          {pdfFiles.map((file, index) => (
            <Text key={index} style={styles.fileNameText}>📄 {file.name}</Text>
          ))}
        </View>
      )}

      <TextInput
        style={styles.input}
        placeholder="Client Name"
        value={clientName}
        onChangeText={setClientName}
      />

      <TextInput
        style={styles.input}
        placeholder="Client Age"
        value={clientAge}
        onChangeText={setClientAge}
        keyboardType="numeric"
      />

      <TextInput
        style={[styles.input, styles.textArea]}
        placeholder="Describe the claim (e.g., met with an accident)..."
        value={claimFactors}
        onChangeText={setClaimFactors}
        multiline
      />

      <TouchableOpacity style={[styles.button, styles.analyzeButton]} onPress={uploadAndAnalyze}>
        <Text style={styles.buttonText}>2. Analyze Claim</Text>
      </TouchableOpacity>

      {loading && <ActivityIndicator size="large" color="#0000ff" style={{ marginTop: 20 }} />}

      {answer !== '' && (
        <View style={styles.resultBox}>
          <Text style={styles.resultHeader}>AI Analysis:</Text>
          <Text style={styles.resultText}>{answer}</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 20, backgroundColor: '#f5f5f5', paddingTop: 60 },
  header: { fontSize: 24, fontWeight: 'bold', marginBottom: 20, textAlign: 'center', color: '#333' },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#ccc', padding: 15, borderRadius: 8, marginBottom: 15, fontSize: 16 },
  textArea: { height: 100, textAlignVertical: 'top' },
  button: { backgroundColor: '#007bff', padding: 15, borderRadius: 8, alignItems: 'center', marginBottom: 15 },
  analyzeButton: { backgroundColor: '#28a745' },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  fileListContainer: { marginBottom: 15, paddingHorizontal: 5 },
  fileNameText: { fontSize: 14, color: '#555', marginBottom: 4 },
  resultBox: { marginTop: 20, padding: 20, backgroundColor: '#fff', borderRadius: 8, borderWidth: 1, borderColor: '#ddd' },
  resultHeader: { fontSize: 18, fontWeight: 'bold', marginBottom: 10, color: '#333' },
  resultText: { fontSize: 16, color: '#555', lineHeight: 24 }
});